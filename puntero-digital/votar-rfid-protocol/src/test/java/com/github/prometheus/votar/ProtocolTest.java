package com.github.prometheus.votar;

import static org.hamcrest.CoreMatchers.*;
import static org.junit.Assert.assertThat;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;

import org.junit.Test;

import com.github.prometheus.votar.Protocol.DataType;

public class ProtocolTest {

  @Test
  public void writeAndRead() throws Exception {
    ByteArrayOutputStream output = new ByteArrayOutputStream(
        Protocol.BLOCKS * Protocol.BLOCK_SIZE);
    Protocol.write(output, DataType.VOTE, "MSA la tiene adentro");

    ByteArrayInputStream input = new ByteArrayInputStream(output.toByteArray());
    assertThat(Protocol.read(input), is("MSA la tiene adentro"));
  }
}
