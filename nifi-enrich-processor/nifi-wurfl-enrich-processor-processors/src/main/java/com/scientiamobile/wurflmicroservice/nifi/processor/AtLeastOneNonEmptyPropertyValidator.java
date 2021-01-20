package com.scientiamobile.wurflmicroservice.nifi.processor;

import org.apache.commons.lang.ArrayUtils;
import org.apache.nifi.components.PropertyDescriptor;
import org.apache.nifi.components.ValidationContext;
import org.apache.nifi.components.ValidationResult;
import org.apache.nifi.components.Validator;
import org.apache.nifi.util.StringUtils;

import java.util.Map;

public class AtLeastOneNonEmptyPropertyValidator {

    public ValidationResult validate(ValidationContext validationContext, PropertyDescriptor... propertiesToValidate) {

        if (ArrayUtils.isEmpty(propertiesToValidate)){
            return new ValidationResult.Builder()
                    .subject("general")
                    .valid(false)
                    .explanation("Cannot create AtLeastOneValidator without a list of properties to validate").build();
        }

        String[] propertiesDisplayNames = new String[propertiesToValidate.length];
        for(int i = 0; i < propertiesToValidate.length; i++){
            propertiesDisplayNames[i] = propertiesToValidate[i].getDisplayName();
        }
        String propertyListForMessage = String.join(",", propertiesDisplayNames);

        Map<String,String> properties = validationContext.getAllProperties();
        for(PropertyDescriptor property: propertiesToValidate){
            String propertyValue = properties.get(property.getName());
            if (StringUtils.isNotBlank(propertyValue)){
                return new ValidationResult.Builder()
                        .subject("At least one of " + propertyListForMessage)
                        .valid(true)
                        .explanation(property.getName() + " has a non blank value ").build();
            }
        }

        // Non was valid
        return new ValidationResult.Builder()
                .subject("One of the properties: " + propertyListForMessage)
                .valid(false)
                .explanation(" at least one of them must have a non blank value ")
                .build();
    }
}
