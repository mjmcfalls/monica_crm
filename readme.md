### Monica CRM
My deployment of [Monica CRM](https://www.monicahq.com/)

The dev directory is a local docker build of Monica using Small Step CA to generate testing certificates for HTTPs to test HTTP redirection in traefik.  

I could not get traefik to see the certificate bundle when loaded to the base container; instead I had to build custom traefik image with the certificate bundle loaded and installed.  The docker file to build the custom image is under ```Dev\traefik_build```

The AWS install is loosely based on the directions found at [https://dev.to/lautmat/monica-crm-goes-on-aws-with-a-low-cost-docker-deployment-using-ecs-s3-ses-and-aurora-4183](https://dev.to/lautmat/monica-crm-goes-on-aws-with-a-low-cost-docker-deployment-using-ecs-s3-ses-and-aurora-4183).  

I added some additional configuration information for my AWS instance to appease myself.  

Specifically, I noticed the reminders do not fire with the Aurora serverless DB.  I created a bash script to warm up the Aurora database before the reminders are scheduled to fire.  I believe this should temporarily help me.  
I, also, used a larger reserved instance; the larger instance cost more, but the perceived increase responsiveness of the app was worth the additional costs for me.

Crontab command on the linux host to run the daily schedules in the Monica container: 
```/usr/bin/docker exec -it `docker ps | grep  monica | cut -d " " -f 1` php artisan schedule:run```

I went with the linux host running the crontab, because I wanted a daily digest and not per person emails.  I have a separate python script in AWS Lambda that is triggered daily by AWS Eventbridge. 