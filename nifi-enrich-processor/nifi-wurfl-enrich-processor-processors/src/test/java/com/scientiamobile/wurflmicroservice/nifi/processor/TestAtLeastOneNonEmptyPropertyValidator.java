package com.scientiamobile.wurflmicroservice.nifi.processor;

import org.apache.nifi.components.PropertyDescriptor;
import org.apache.nifi.components.ValidationContext;
import org.apache.nifi.components.ValidationResult;
import org.apache.nifi.components.Validator;
import org.apache.nifi.processor.util.StandardValidators;
import org.junit.Assert;
import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class TestAtLeastOneNonEmptyPropertyValidator {

    public static final PropertyDescriptor PROP_01 = new PropertyDescriptor
            .Builder().name("PROP_01")
            .displayName("Prop 01")
            .description("Description of property 01")
            .required(false)
            .addValidator(Validator.VALID)
            .build();
    public static final PropertyDescriptor PROP_02 = new PropertyDescriptor
            .Builder().name("PROP_02")
            .displayName("Prop 02")
            .description("Description of property 02")
            .required(false)
            .addValidator(Validator.VALID)
            .build();

    public static final PropertyDescriptor PROP_03 = new PropertyDescriptor
            .Builder().name("PROP_03")
            .displayName("Prop 03")
            .description("Description of property 03")
            .required(false)
            .addValidator(Validator.VALID)
            .build();


    @Test
    public void validNotEmptyTest(){
        AtLeastOneNonEmptyPropertyValidator validator = new AtLeastOneNonEmptyPropertyValidator();
        Map<String,String> properties = new HashMap<>();
        properties.put("PROP_02", "value02");
        ValidationContext ctx = mock(ValidationContext.class);
        when(ctx.getAllProperties()).thenReturn(properties);
        ValidationResult result = validator.validate(ctx, PROP_01, PROP_02, PROP_03);
        Assert.assertTrue(result.isValid());
    }

    @Test
    public void invalidNotEmptyTest(){
        AtLeastOneNonEmptyPropertyValidator validator = new AtLeastOneNonEmptyPropertyValidator();
        Map<String,String> properties = new HashMap<>();
        ValidationContext ctx = mock(ValidationContext.class);
        when(ctx.getAllProperties()).thenReturn(properties);

        ValidationResult result = validator.validate(ctx, PROP_01, PROP_02, PROP_03);
        Assert.assertFalse(result.isValid());
    }
}
