package com.github.prometheus.votar;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.io.OutputStream;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.Validate;

/** Represents the VOT.AR voting ballots protocol.
 */
public class Protocol {

  /** Number of blocks within the RFID tag. */
  public static final int BLOCKS = 28;

  /** Number of available blocks to write data. */
  public static final int DATA_BLOCKS = 25;

  /** Size of each block within the RFID tag. */
  public static final int BLOCK_SIZE = 4;

  /** Id used as protocol identifier. */
  public static final byte TOKEN = 0x1C;

  /** Verification identifier. */
  public static final byte[] VERIFIER = "W_OK".getBytes();

  /** Offset of the protocol identifier. */
  public static final int OFFSET_TOKEN = 0x0;

  /** Offset of the custom data type identifier. */
  public static final int OFFSET_DATA_TYPE = 0x1;

  /** Offset of the custom data length. */
  public static final int OFFSET_DATA_LENGTH = 0x3;

  /** Offset of the custom data CRC. */
  public static final int OFFSET_CRC = 0x4;

  /** Position where custom data starts. */
  public static final int OFFSET_DATA = 0x7;

  /** Offset of the verification identifier. */
  public static final int OFFSET_VERIFIER = 0x6C;

  /** Supported data types */
  public enum DataType {
    /** The data represents a vote. */
    VOTE(0x1),
    /** The data represents an MSA user information. */
    MSA_USER(0x2),
    /** The data represents user information related to the president
     * of a single location. */
    PRESIDENT(0x3),
    /** The data has re-counting information. */
    RECOUNTING(0x4),
    /** The data has opening information. */
    OPENING(0x5),
    /** The data is related to a DEMO version of VOT.AR. */
    DEMO(0x6);

    final int value;

    private DataType(int value) {
      this.value = value;
    }

    public static DataType fromValue(int value) {
      for (DataType dataType : values()) {
        if (dataType.value == value) {
          return dataType;
        }
      }
      throw new RuntimeException("Invalid data type value: " + value);
    }
  }

  /** Writes data to the specified output stream using the protocol. It
   * is thread-safe.
   * @param output Output stream to write. Cannot be null.
   * @param dataType Data type. Cannot be null.
   * @param data Data to write. Cannot be null or empty.
   */
  public static void write(OutputStream output, DataType dataType, String data) {
    ProtocolWriter writer = new ProtocolWriter(output, dataType);

    try {
        writer.write(data);
    } catch (Exception cause) {
        throw new RuntimeException("Cannot write data", cause);
    } finally {
      IOUtils.closeQuietly(writer);
    }
  }

  /** Reads the custom data from the specified input stream. It is
   * thread-safe.
   * @param input Input to read. Cannot be null.
   * @return The custom data, never null.
   */
  public static String read(InputStream input) {
    ProtocolReader reader = new ProtocolReader(input);
    try {
        return reader.getDataAsString();
    } finally {
        IOUtils.closeQuietly(reader);
    }
  }
}
