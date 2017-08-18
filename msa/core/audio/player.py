""" audioplayer.py
    Módulo para reproducción de archivos de sonido vía ALSA
"""
# Importante para el cálculo del sleep en run()
import time

from alsaaudio import PCM, Mixer, ALSAAudioError, MIXER_CHANNEL_ALL
from datetime import datetime
from threading import Thread
from wave import open as waveOpen

from msa.core.logging import get_logger
from msa.core.audio.settings import SPEECH_PAUSE
from msa.core.audio.constants import VALORES_VOLUMEN, MIXER_PRIO

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
        self.callback_fin_cola = None

    def __init_alsa(self):
        try:
            self._device = PCM()
        except ALSAAudioError as e:
            logger.error('ERROR: Error al inicializar dispositivo ALSA: %s' %
                         str(e))
            return
        else:
            for mixer in MIXER_PRIO:
                try:
                    self._mixers[mixer] = Mixer(mixer)
                except ALSAAudioError as e:
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
            try:
                wav_file = waveOpen(file_name, 'rb')
                nc, sw, fr, nf, comptype, compname = wav_file.getparams()
                self._cache[file_name] = WavData(nc, fr, nf,
                                                 wav_file.readframes(nf))
                wav_file.close()
            except Exception as exc:
                self._cache[file_name] = None
                print(exc)
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
            if len(self._queue):
                now_filename, now_message = self._queue.pop(0)
                if now_message == WavPlayer.PAUSE_TOKEN:
                    time.sleep(SPEECH_PAUSE)
                    continue
                wav = self._get_wav(now_filename)
                if wav is not None:
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
                if not len(self._queue) and self.callback_fin_cola is not None:
                    self.callback_fin_cola()
            # NO SACAR, sino audioplayer se come el 100% de cpu
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
        """ Sets volume """
        mixer_name = self._default_mixer
        num_vals = len(VALORES_VOLUMEN)
        if mixer_name is not None and level >= 0 and level <= num_vals:
            mixer = self._mixers[mixer_name]
            log_value = VALORES_VOLUMEN[level]
            mixer.setvolume(log_value, MIXER_CHANNEL_ALL)

    def get_volume(self, mixer=None):
        """ Returns the volume in a Mixer. If mixer is None, returns the volume
            from the most relevant, the default """
        index = None
        if mixer is None:
            mixer = self._default_mixer
        if mixer is not None:
            log_value = int(self._mixers[mixer].getvolume()[0])
            try:
                index = VALORES_VOLUMEN.index(log_value)
            except ValueError:
                pass
        return index

    def registrar_callback_fin_cola(self, callback):
        """Registra un callback que será llamado la próxima vez que se vacíe la
        cola de mensajes."""
        def _inner():
            callback()
            self.callback_fin_cola = None

        self.callback_fin_cola = _inner
