package com.scientiamobile.wurflmicroservice.nifi.processor;

import com.scientiamobile.wurfl.wmclient.WmClient;
import org.apache.nifi.annotation.lifecycle.OnScheduled;
import org.apache.nifi.processor.ProcessContext;
import org.apache.nifi.util.TestRunner;
import org.apache.nifi.util.TestRunners;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;


import java.io.IOException;

import static org.mockito.Mockito.mock;

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
        testRunner = TestRunners.newTestRunner(wurflDeviceEnrich);
    }

    class TestableWURFLDeviceEnrich extends WURFLDeviceEnrichProcessor {
        @OnScheduled
        public void onScheduled(ProcessContext context) {
            wmClientRef.set(wmClient);
        }
    }

}
