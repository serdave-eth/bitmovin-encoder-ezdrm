# Description

Script for encoding an mp4 file using Bitmovin and EZDRM

## Getting Started

Use this EZDRM guide to get set up: https://hs.ezdrm.com/hubfs/Documentation/EZDRM%20Bitmovin%20Encoding%20V2.pdf?hsLang=en

A local copy of the guide is in this repo.

A couple "gotchas" in the guide:

1. For the S3 bucket, you need to have Object Ownership has ACL enabled. 
2. For the S3 bucket, you need to have CORS access. This is the easiest CORS access to have: 

[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3000
    }
]

CORS access can be found under the Permissions tab for the S3 bucket.

## Running the script

Install the bitmovin_api_sdk python package

Add input parameters to lines 12-25 of the main script (cenc_drm_content_protection.py) per the comments in the code and the EZDRM guide

run the main script. If the script ran successfully you should get the following output to your console: 

Encoding status is Status.FINISHED (progress: 100 %)
Encoding finished successfully

## Testing the encoded video

Go to https://bitmovin.com/demos/drm

1. Select "Dash"
2. Manifest URL: the url of the s3 object of the .mpd file (can be found in the output S3 bucket). 
3. License Server URL: Widevine Server URL that EZDRM produces in step 2 of the EZDRM guide. 

## Notes

This script is using dropbox for hosting the input file, but any file service that allows HTTPS will work. I think S3 will work for this too but was encountering some errors. 

Original script: https://github.com/bitmovin/bitmovin-api-sdk-examples/blob/main/python/src/cenc_drm_content_protection.py

Main change I made to the script was hardcoding the input values. This is the script that should be used instead of the python script referenced in the EZDRM guide.