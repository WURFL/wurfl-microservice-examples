package com.scientiamobile.wurflmicroservice.nifi.processor;

import com.scientiamobile.wurfl.wmclient.WmClient;
import com.scientiamobile.wurfl.wmclient.WmException;
import org.apache.nifi.annotation.lifecycle.OnScheduled;
import org.apache.nifi.processor.ProcessContext;
import org.apache.nifi.util.MockFlowFile;
import org.apache.nifi.util.TestRunner;
import org.apache.nifi.util.TestRunners;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@RunWith(PowerMockRunner.class)
@PrepareForTest({WURFLDeviceEnrichProcessor.class})
public class TestWURFLDeviceEnrichProcessor {

    WmClient wmClient;
    WURFLDeviceEnrichProcessor wurflDeviceEnrich;
    private TestRunner testRunner;

    @Before
    public void setUp() throws Exception {
        wmClient = mock(WmClient.class);
        wurflDeviceEnrich = new TestableWURFLDeviceEnrich();
        wurflDeviceEnrich.wmClientRef = new AtomicReference<>();
        testRunner = TestRunners.newTestRunner(wurflDeviceEnrich);
    }

    @Test
    public void wmExceptionFlowsToFailure() throws WmException {

        testRunner.setProperty(WURFLDeviceEnrichProcessor.WM_SCHEME, "http");
        testRunner.setProperty(WURFLDeviceEnrichProcessor.WM_HOST, "localhost");
        testRunner.setProperty(WURFLDeviceEnrichProcessor.WM_PORT, "9080");
        testRunner.setProperty(WURFLDeviceEnrichProcessor.INPUT_ATTR_TYPE, "attribute name");
        testRunner.setProperty(WURFLDeviceEnrichProcessor.INPUT_ATTR_NAME, "http.headers.User-Agent");

        String ua = "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.62 Mobile Safari/537.36";
        Map<String,String> headers = new HashMap<>();
        headers.put("User-Agent", ua);
        WmException e = new WmException("Detection failed");
        when(wmClient.lookupHeaders(headers)).thenThrow(e);
        final Map<String, String> attributes = new HashMap<>();

        attributes.put("http.headers.User-Agent", ua);

        testRunner.enqueue(new byte[0], attributes);
        testRunner.run();

        List<MockFlowFile> failure = testRunner.getFlowFilesForRelationship(WURFLDeviceEnrichProcessor.FAILURE);
        assertEquals(1, failure.size());
        String failAttr = failure.get(0).getAttribute(WURFLDeviceEnrichProcessor.FAILURE_ATTR_NAME);
        assertNotNull(failAttr);
        assertEquals(failAttr, "Detection failed");
        List<MockFlowFile> success = testRunner.getFlowFilesForRelationship(WURFLDeviceEnrichProcessor.SUCCESS);
        assertEquals(0, success.size());



    }

    class TestableWURFLDeviceEnrich extends WURFLDeviceEnrichProcessor {
        @OnScheduled
        public void onScheduled(ProcessContext context) {
            wmClientRef.set(wmClient);
        }
    }

}
