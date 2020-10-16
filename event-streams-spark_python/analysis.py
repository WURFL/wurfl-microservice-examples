#!/usr/bin/env python
# coding: utf-8

# In[82]:

import pandas as pd

df = pd.read_csv('evs_records.csv')

# In[83]:


df_os = df['device_os'].value_counts().reset_index()
df_os.columns = ['OS', 'Count']

# In[84]:


df_os_version = df[['device_os', 'device_os_version']].value_counts().reset_index()
df_os_version.columns = ['OS', 'Version', 'Count']

# In[85]:


df_smartphone_screensize = \
    df[(df['is_smartphone'] is True) | (df['is_mobile'] is True) | (df['is_phone'] is True) & (
            df['is_tablet'] is False)][
        ['resolution_height', 'resolution_width']].value_counts()[:5].reset_index()
df_smartphone_screensize.columns = ['Height', 'Width', 'Count']

# In[86]:


df_tablet_screensize = df[df['is_tablet'] is True][['resolution_height', 'resolution_width']].value_counts()[
                       :5].reset_index()
df_tablet_screensize.columns = ['Height', 'Width', 'Count']

# In[87]:

df_os.to_csv('os_counts.csv', index=False)
df_os_version.to_csv('os_version_counts.csv', index=False)
df_smartphone_screensize.to_csv('smartphone_top_5_screensizes.csv', index=False)
df_tablet_screensize.to_csv('tablet_top_5_screensizes.csv', index=False)
