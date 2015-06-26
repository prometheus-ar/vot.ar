package com.github.prometheus.votar;

import java.io.IOException;
import java.io.OutputStream;
import java.io.Writer;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.zip.CRC32;

import org.apache.commons.lang3.ArrayUtils;
import org.apache.commons.lang3.Validate;

import com.github.prometheus.votar.Protocol.DataType;

/** Writes a data stream ready to use with VOT.AR voting ballots. It
 * implements the following specification: http://justpaste.it/lw65
 *
 * It keeps a memory buffer until the writer is closed, then it writes the data
 * out to the {@link OutputStream}.
 */
public class ProtocolWriter extends Writer {

  /** Buffer to write data before flushing to the output stream. */
  private final ByteBuffer buffer = ByteBuffer
      .allocate(Protocol.BLOCKS * Protocol.BLOCK_SIZE);

  /** Custom data buffer. */
  private final ByteBuffer data = ByteBuffer
      .allocate(Protocol.DATA_BLOCKS * Protocol.BLOCK_SIZE);

  /** Output stream to write data to, never null. */
  private OutputStream output;

  /** Type of data to write, never null. */
  private DataType dataType;

  /** Indicates whether this writer is closed. */
  private boolean closed;

  /** Creates a protocol writer for the specified data type.
   * @param output
   * @param dataType Type of data to write. Cannot be null.
   */
  public ProtocolWriter(OutputStream output, DataType dataType) {
    Validate.notNull(output, "The output stream cannot be null.");
    Validate.notNull(dataType, "The data type cannot be null.");

    this.output = output;
    this.dataType = dataType;

    buffer.order(ByteOrder.BIG_ENDIAN);
  }

  /** {@inheritDoc}
   */
  @Override
  public void write(char[] cbuf, int offset, int len) throws IOException {
    Validate.isTrue(closed == false, "Write already closed");

    for (int i = 0; i < cbuf.length; i++) {
      data.putChar(offset + i, cbuf[i]);
    }
  }

  /** Writes a byte array at the specified position.
   * @param values Bytes to write. Cannot be null.
   * @param offset Position to start writing.
   */
  public void write(byte[] values, int offset) {
    Validate.isTrue(closed == false, "Write already closed");

    for (int i = 0; i < values.length; i++) {
      data.put(offset + i, values[i]);
    }
  }

  /** {@inheritDoc}
   */
  @Override
  public void write(String str) throws IOException {
    write(str.getBytes());
  }

  /** Writes a byte array at the current position.
   * @param values Bytes to write. Cannot be null.
   */
  public void write(byte[] values) {
    Validate.isTrue(closed == false, "Write already closed");

    for (int i = 0; i < values.length; i++) {
      data.put(values[i]);
    }
  }

  /** Writes the data into the memory buffer. */
  @Override
  public void flush() throws IOException {
    Validate.isTrue(closed == false, "Write already closed");

    byte[] dataBytes = getData();

    buffer.put(Protocol.OFFSET_TOKEN, Protocol.TOKEN);
    buffer.putShort(Protocol.OFFSET_DATA_TYPE, (short) dataType.value);
    buffer.put(Protocol.OFFSET_DATA_LENGTH, (byte) dataBytes.length);
    buffer.putLong(Protocol.OFFSET_CRC, crc(dataBytes));
    write(buffer, Protocol.OFFSET_DATA, dataBytes);
    write(buffer, Protocol.OFFSET_VERIFIER, Protocol.VERIFIER);
  }

  /** Flushes and writes the data into the output stream, then closes it. */
  @Override
  public void close() throws IOException {
    flush();
    output.write(buffer.array());
    output.close();
    closed = true;
  }

  private void write(ByteBuffer buffer, int offset, byte[] values) {
    for (int i = 0; i < values.length; i++) {
      buffer.put(offset + i, values[i]);
    }
  }

  private long crc(byte[] values) {
    CRC32 crc = new CRC32();
    crc.update(values);
    return crc.getValue();
  }

  private byte[] getData() {
    byte[] dataBytes = data.array();
    byte[] result = new byte[] {};

    for (int i = 0; i < dataBytes.length; i++) {
      if (dataBytes[i] == 0) {
        result = new byte[i - 1];
        return ArrayUtils.subarray(dataBytes, 0, i);
      }
    }

    return result;
  }
}
