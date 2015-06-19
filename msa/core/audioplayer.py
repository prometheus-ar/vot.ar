# coding: utf-8
""" audioplayer.py
    Módulo para reproducción de archivos de sonido vía ALSA
"""
# Importante para el cálculo del sleep en run()
from __future__ import division
import time
from datetime import datetime
from threading import Thread
from alsaaudio import PCM, Mixer, ALSAAudioError, MIXER_CHANNEL_ALL
from wave import open as waveOpen

from msa import get_logger
from msa.core.settings import SPEECH_PAUSE

logger = get_logger("core")


class WavData:

    def __init__(self, nchannels, frate, nframes, data):
        self.nchannels = nchannels
        self.frate = frate
        self.data = data
        self.nframes = nframes


class WavPlayer(Thread):

    """ Un thread que ejecuta archivos de sonido.

        A medida que recibe mensajes para ejecutar archivos wav, los guarda en
        un cache interno asi no los tiene que cargar en cada repeticion.

        Para ejecutar un wav, se debe llamar al metodo play(file), donde file
        es la direccion completa al archivo wav. También se pueden encolar
        varios wav a decir en una lista mediante el método queue_play().
    """

    PAUSE_TOKEN = ''
    MIXER_PRIO = ('Master', 'PCM', 'Headphone')

    def __init__(self, as_daemon=True):
        Thread.__init__(self)
        self.daemon = as_daemon
        self._cache = {}
        self.__running = False
        self._device = None
        self._mixers = {}
        self._default_mixer = None
        self._queue = []
        self.__init_alsa()

    def __init_alsa(self):
        try:
            self._device = PCM()
        except ALSAAudioError, e:
            logger.error('ERROR: Error al inicializar dispositivo ALSA: %s' %
                         str(e))
            return
        else:
            for mixer in WavPlayer.MIXER_PRIO:
                try:
                    self._mixers[mixer] = Mixer(mixer)
                except ALSAAudioError, e:
                    err = 'Warning: Error al inicializar mixer ALSA: %s'
                    logger.warning(err % str(e))
                else:
                    if self._default_mixer is None:
                        self._default_mixer = mixer

    def _get_wav(self, file_name):
        """ Returns a WaveData instance from the self._wav_file property,
            keeping it in a cache dictionary for subsequent calls.
        """
        if file_name not in self._cache:
            wav_file = waveOpen(file_name, 'rb')
            nc, sw, fr, nf, comptype, compname = wav_file.getparams()
            self._cache[file_name] = WavData(nc, fr, nf,
                                             wav_file.readframes(nf))
            wav_file.close()
        return self._cache[file_name]

    def _play(self, wav):
        """ Plays a sound in a ALSA device """
        self._device.setchannels(wav.nchannels)
        self._device.setrate(wav.frate)
        self._device.setperiodsize(wav.nframes)
        self._device.write(wav.data)

    def run(self):
        """ Starts the loop waiting for audio files to be played """
        self.__running = True
        while self.__running:
            if self._queue:
                now_filename, now_message = self._queue.pop(0)
                if now_message == WavPlayer.PAUSE_TOKEN:
                    time.sleep(SPEECH_PAUSE)
                    continue
                wav = self._get_wav(now_filename)
                inicio = datetime.now()
                self._play(wav)
                # calculamos cuanto tiempo quedo "colgado" hasta
                # volver del _play, para descontar eso de la espera
                # (el _play empieza a reproducir pero no retorna
                # instantaneamente si el archivo es grande)
                dcarga = datetime.now() - inicio
                # asumiendo que la carga no dura mas de un dia
                segundos_carga = dcarga.seconds + \
                    dcarga.microseconds / 1000000.0
                sleep_time = (wav.nframes / wav.frate) - segundos_carga
                if sleep_time > 0:
                    time.sleep(sleep_time)
            # NO SACAR, sino audioplayer se coma el 100% de cpu
            time.sleep(0.1)

    def play(self, wav_file):
        """ Assigns a wave file to be played.

            Arguments:
            wav_file -- File path of the audio file.
        """
        if wav_file is not None:
            self._queue = [(wav_file, None)]

    def queue_play(self, wav_file, mensaje=None):
        if wav_file is not None:
            self._queue.append((wav_file, mensaje))

    def empty_queue(self):
        self._queue = []

    def stop(self):
        """ Stops the thread. It can't be started again, so it also closes
            the opened audio device """
        self.empty_queue()
        self.__running = False
        self.close()

    def pending_files(self):
        return len(self._queue) > 0

    def close(self):
        """ Closes the audio output opened in the constructor.
            Useful to call from outside if as_daemon=False
            (instantiated only to set the volume for example)
        """
        if self._device:
            self._device.close()

    def set_volume(self, level):
        """ Sets volume for both Master, PCM Mixer and all its channels """
        if int(level) >= 0 and int(level) <= 100:
            for mixer in self._mixers.values():
                mixer.setvolume(level, MIXER_CHANNEL_ALL)

    def get_volume(self, mixer=None):
        """ Returns the volume in a Mixer. If mixer is None, returns the volume
            from the most relevant, the default """
        if mixer is None:
            mixer = self._default_mixer
        return int(self._mixers[mixer].getvolume()[0])


def test_module(file, volume=None):
    logger.info('Testing ALSA')
    player = WavPlayer(as_daemon=False)
    player.start()
    player.play(file)
    time.sleep(1)
    player.stop()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python audioplayer.py file.wav [volume]')
        sys.exit(1)
    volume = None
    if len(sys.argv) >= 3:
        volume = int(sys.argv[2])
    test_module(sys.argv[1], volume)
