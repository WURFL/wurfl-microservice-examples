/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.scientiamobile.wurflmicroservice.nifi.processor;

import org.apache.nifi.annotation.behavior.ReadsAttribute;
import org.apache.nifi.annotation.behavior.WritesAttribute;
import org.apache.nifi.annotation.behavior.WritesAttributes;
import org.apache.nifi.annotation.lifecycle.*;
import org.apache.nifi.components.PropertyDescriptor;
import org.apache.nifi.components.Validator;
import org.apache.nifi.flowfile.FlowFile;
import org.apache.nifi.annotation.documentation.CapabilityDescription;
import org.apache.nifi.annotation.documentation.Tags;
import org.apache.nifi.logging.ComponentLog;
import org.apache.nifi.processor.exception.ProcessException;
import org.apache.nifi.processor.AbstractProcessor;
import org.apache.nifi.processor.ProcessContext;
import org.apache.nifi.processor.ProcessSession;
import org.apache.nifi.processor.ProcessorInitializationContext;
import org.apache.nifi.processor.Relationship;
import org.apache.nifi.processor.util.StandardValidators;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;

import com.scientiamobile.wurfl.wmclient.*;

@Tags({"http", "https", "request", "listen", "WURFL", "web service", "attributes"})
@CapabilityDescription("Processor that enriches data from HTTP requests passed in the flow files with data coming from WURFL Microservice")
@ReadsAttribute(attribute = "http.headers.XXX", description = "Each of the HTTP Headers exposed by HandleHttpRequest processor")
@WritesAttributes({
        @WritesAttribute(attribute = "wurfl.XXX", description = "Each of the WURFL capabilities exposed by WURFL Microservice will be added as "
                + "attribute, prefixed with \"wurfl.\" For example, if the WURFL capability named \"brand_name\", then the value "
                + "will be added to an attribute named \"wurfl.brand_name\""),
        @WritesAttribute(attribute = "failure.cause", description = "Description of WURFL Microservice error in case of exception occurred in the detection process")
})
public class WURFLDeviceEnrichProcessor extends AbstractProcessor {

    private final static String WURFL_ATTR_PREFIX = "wurfl.";
    private final static String HTTP_HEADER_ATTR_PREFIX = "http.headers.";
    private static final String FAILURE_ATTR_NAME = "failure.cause";


    private AtomicReference<WmClient> wmClientRef;
    private ComponentLog logger;
    private Map<String, String> currentConfiguration = new ConcurrentHashMap<>();


    // Let's add all the configuration properties needed by WURFL Microservice to be created and used by the NiFi processor.
    // These properties are filled in the Processor creation wizard in NiFi webapp UI

    public static final PropertyDescriptor WM_SCHEME = new PropertyDescriptor
            .Builder().name("WM_SCHEME")
            .displayName("WM server scheme")
            .description("Connection protocol scheme used to connect to WURFL Microservice server (http/https)")
            .required(true)
            .addValidator(StandardValidators.NON_EMPTY_VALIDATOR)
            .defaultValue("http")
            .build();

    public static final PropertyDescriptor WM_HOST = new PropertyDescriptor
            .Builder().name("WM_HOST")
            .displayName("WM server host")
            .description("Host or IP address used to connect to WURFL Microservice server")
            .required(true)
            .addValidator(StandardValidators.NON_EMPTY_VALIDATOR)
            .build();

    public static final PropertyDescriptor WM_PORT = new PropertyDescriptor
            .Builder().name("WM_PORT")
            .displayName("WM server port")
            .description("Port number used to connect to WURFL Microservice server")
            .required(true)
            .addValidator(StandardValidators.PORT_VALIDATOR)
            .build();

    public static final PropertyDescriptor WM_BASE_PATH = new PropertyDescriptor
            .Builder().name("WM_BASE_PATH")
            .displayName("WM base base path")
            .description("URL segment that is needed by your URL address to connect to WURFL Microservice server. In most cases it's not needed")
            .required(false)
            .addValidator(Validator.VALID)
            .defaultValue("")
            .build();

    public static final PropertyDescriptor WM_CACHE_SIZE = new PropertyDescriptor
            .Builder().name("WM_CACHE_SIZE")
            .displayName("WM cache size")
            .description("Cache size for WURFL Microsroservice client instance")
            .required(false)
            .addValidator(StandardValidators.POSITIVE_INTEGER_VALIDATOR)
            .defaultValue("100000")
            .build();

    public static final Relationship SUCCESS = new Relationship.Builder()
            .name("SUCCESS")
            .description("Success relationship, used when WURFL detection process applied to the flow file succeeds")
            .build();

    public static final Relationship FAILURE = new Relationship.Builder()
            .name("FAILURE")
            .description("Failure relationship, used when WURFL detection process applied to the flow file fails for some reason")
            .build();

    private List<PropertyDescriptor> descriptors;

    private Set<Relationship> relationships;

    private final List<String> triggerClientResetProps = new ArrayList<>();

    @Override
    protected void init(final ProcessorInitializationContext context) {

        logger = getLogger();

        triggerClientResetProps.add(WM_SCHEME.getName());
        triggerClientResetProps.add(WM_HOST.getName());
        triggerClientResetProps.add(WM_PORT.getName());
        triggerClientResetProps.add(WM_BASE_PATH.getName());

        final List<PropertyDescriptor> descriptors = new ArrayList<>();
        descriptors.add(WM_SCHEME);
        descriptors.add(WM_HOST);
        descriptors.add(WM_PORT);
        descriptors.add(WM_BASE_PATH);
        descriptors.add(WM_CACHE_SIZE);
        this.descriptors = Collections.unmodifiableList(descriptors);

        final Set<Relationship> relationships = new HashSet<>();
        relationships.add(SUCCESS);
        relationships.add(FAILURE);
        this.relationships = Collections.unmodifiableSet(relationships);
    }

    @Override
    public Set<Relationship> getRelationships() {
        return this.relationships;
    }

    @Override
    public final List<PropertyDescriptor> getSupportedPropertyDescriptors() {
        return descriptors;
    }

    @OnScheduled
    public void onScheduled(final ProcessContext context) throws WmException {
        //logger.info("------------------------ ON SCHEDULED ---------------------------");
        currentConfiguration = fromContext(context);

        if (wmClientRef == null || wmClientRef.get() == null) {
            logger.warn("Recreating WM client in onSchedule method");
            if (!createWmClient(currentConfiguration)) {
                return;
            }
            wmClientRef.get().setCacheSize(Integer.parseInt(currentConfiguration.get(WM_CACHE_SIZE.getName())));
        }
    }

    @Override
    public void onPropertyModified(final PropertyDescriptor descriptor, final String oldValue, final String newValue) {

        // it seems weird, but sometimes this gets called even when property has not been changed,
        // as in this issue https://issues.apache.org/jira/browse/NIFI-7123
        if (oldValue == null || newValue == null || oldValue.equals(newValue)) {
            return;
        }

        // create a copy of the config config and replace the updated value
        Map<String, String> newConfig = new ConcurrentHashMap<>(currentConfiguration);
        newConfig.put(descriptor.getName(), newValue);

        // In case the changed property is just cache size, we reset the cache
        if (descriptor.getName().equals(WM_CACHE_SIZE.getName())) {
            logger.warn("Resetting WM client cache in onPropertyModified method");
            wmClientRef.get().setCacheSize(Integer.parseInt(newValue));
            // all other properties in this list trigger a new client creation
        } else if (triggerClientResetProps.contains(descriptor.getName())) {
            try {
                wmClientRef.get().destroyConnection();
                wmClientRef = null;
            } catch (WmException e) {
                logger.warn("Unable to destroy WM client", e);
            }
            logger.warn("Recreating WM client in onPropertyModified method");
            if (createWmClient(newConfig)) {
                currentConfiguration = newConfig;
            }
        }
    }

    /*
     * Creates a new instance of a WM client. It returns false if some exception occurs (ie: connection exception),
     * false otherwise. Logs any error on Apache NiFi log at $NIFI_HOME/logs/nifi-app.log
     */
    private boolean createWmClient(Map<String, String> config) {

        try {
            wmClientRef = new AtomicReference<>();
            WmClient wmClient = WmClient.create(
                    config.get(WM_SCHEME.getName()),
                    config.get(WM_HOST.getName()),
                    config.get(WM_PORT.getName()),
                    config.get(WM_BASE_PATH.getName()));
            wmClientRef.set(wmClient);
            return true;
        } catch (WmException e) {
            logger.error("WURFL Microservice client failed initialized for scheme {}  host:port {}:{}.",
                    new String[]{
                            config.get(WM_SCHEME.getName()), config.get(WM_HOST.getName()), config.get(WM_PORT.getName())});
            e.printStackTrace();
            return false;
        }
    }

    /*
     * This is called when the data flow is removed from NiFi UI or NiFi is shut down
     */
    @OnRemoved
    @OnShutdown
    public void destroyWmClient() {
        logger.info("Stopping WURFL Request Processor");
        if (wmClientRef != null) {
            try {
                wmClientRef.get().destroyConnection();
                wmClientRef = null;
            } catch (WmException e) {
                logger.error(" Error destroying WURFL Microservice client.", e);
            }
        }
        logger.info("WURFL Microservice client stopped and deallocated");
    }

    public static Map<String, String> fromContext(ProcessContext context) {
        Map<String, String> config = new ConcurrentHashMap<>();
        config.put(WM_SCHEME.getName(), context.getProperty(WM_SCHEME).getValue());
        config.put(WM_HOST.getName(), context.getProperty(WM_HOST).getValue());
        config.put(WM_PORT.getName(), context.getProperty(WM_PORT).getValue());
        config.put(WM_BASE_PATH.getName(), context.getProperty(WM_BASE_PATH).getValue());
        config.put(WM_CACHE_SIZE.getName(), context.getProperty(WM_CACHE_SIZE).getValue());
        return config;
    }


    @Override
    public void onTrigger(final ProcessContext context, final ProcessSession session) throws ProcessException {

        FlowFile flowFile = session.get();
        if (flowFile == null) {
            logger.warn("Flow file is null, exiting");
            return;
        }

        logger.info("Reading HTTP attributes header ");
        dumpFlowFileAttributes(flowFile);
        Map<String, String> headers = getHeadersFromFlowFile(flowFile);

        logger.info("Starting WURFL data enrichment");
        if (headers.size() == 0) {
            session.transfer(flowFile, FAILURE);
        } else {
            try {
                Model.JSONDeviceData device = wmClientRef.get().lookupHeaders(headers);
                final Map<String, String> wurflAttributes = new ConcurrentHashMap<>();
                device.capabilities.forEach((key, value) -> wurflAttributes.put(WURFL_ATTR_PREFIX + key, value));
                session.putAllAttributes(flowFile, wurflAttributes);
                logger.info("WURFL data enrichment completed, sending SUCCESS flow");
                session.transfer(flowFile, SUCCESS);
            } catch (WmException e) {
                session.putAttribute(flowFile, FAILURE_ATTR_NAME, e.getMessage());
                session.transfer(flowFile, FAILURE);
            }
        }
    }

    private void dumpFlowFileAttributes(FlowFile flowFile) {
        String sep = "------------------------------------------------------\n";
        final StringBuilder dump = new StringBuilder(sep);
        flowFile.getAttributes().forEach((k, v) -> dump.append(k + " : " + v + "\n"));
        dump.append(sep);
        logger.info(dump.toString());
    }

    private Map<String, String> getHeadersFromFlowFile(FlowFile flowFile) {
        Map<String, String> headers = new ConcurrentHashMap<>();
        for (String hName : wmClientRef.get().getImportantHeaders()) {
            String hValue = flowFile.getAttribute(HTTP_HEADER_ATTR_PREFIX + hName);
            if (hValue != null) {
                headers.put(hName, hValue);
            }
        }
        return headers;
    }
}
