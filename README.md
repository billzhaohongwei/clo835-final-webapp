#CLO835 Final Project: Running Flask-App on EKS Cluster

This repository contains the web templates, docker related files, and Kubernetes manifests for deploying a Flask-based web application on a Amazon EKS. The application retrieves a image from a private S3 bucket and displays it as a background for the web pages. A config map is used to store the values of the url for the images and other configuration values.


#Prerequisites

- AWS Account with policy permissions/IAmRoles for S3, EKS, 
- eksctl installed
- kubectl installed
- Docker installed


Steps:

1. Make sure your credentials are properly set. 
 
   - can use nano ~/.aws/credentials to help set it.

2. Install the eks cluster in the directory using the command below.

   - eksctl create cluster -f eks_config.yaml

3. Build the docker images for both the flask app and the database.
   
   - docker build -t <container_name> .
   - docker build -f Dockerfile_mysql -t <container_name> . 
   
4. Create the customer docker network.
   
   - docker network create --driver bridge my_custom_bridge
  
5. Start MySQL DB
   
   - docker run -d --name mysql-db --network my_custom_bridge -e MYSQL_ROOT_PASSWORD=pw mysql-db-image

6. Export environment variables. Insert AWS credentials here
   
   - export DBHOST=172.18.0.2
   - export DBPORT=3306
   - export DBUSER=root
   - export DATABASE=employees
   - export DBPWD=pw
   - export BACKGROUND_IMAGE_URL=https://<S3_bucket_url>/<image_file>
   - export AWS_ACCESS_KEY_ID=<your own value>
   - export AWS_SECRET_ACCESS_KEY=<your own value>
   - export AWS_SESSION_TOKEN=<your own value>

7. Deploy the frontend app, expose it to external connection via port 8080
   
   - docker run -d -p 8080:81 --name color --network my_custom_bridge -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e BACKGROUND_IMAGE_URL=$BACKGROUND_IMAGE_URL -e DBHOST=$DBHOST -e DBPORT=$DBPORT -e DBUSER=$DBUSER -e DBPWD=$DBPWD web-app

#### Now you can view the webpage via IP of host and port 8080  

8. Enable the AWS EBS CSI (Container Storage Interface) driver in EKS cluster to use Amazon Elastic Block Store (EBS) volumes as Persistent Volume Claims.
   
   - eksctl create addon --name aws-ebs-csi-driver --cluster clo835 --service-account-role-arn arn:aws:iam::[YOUR AWS ACCOUNT]:role/LabRole --force

9. Create namespace for the app
   
   - kubectl create ns final

10. Apply clusterrole and clusterrole binding
   
   - kubectl apply -f clusterrolebinding.yaml -f clusterrole.yaml 

11. Apply secrets and svcs and PVC
   
   - kubectl apply -f serviceaccount.yaml -f secrets.yaml -f configmap.yaml -f mysql-service.yaml -f frontend-loadbalancer.yaml -f pvc-mysql.yaml -n final

12. Apply backend db

   - kubectl apply -f clusterrolebinding.yaml -f clusterrole.yaml 

13. Apply frontend container

   - kubectl apply -f frontend-deployment.yaml -n final 

14. Check resources

   - kubectl get all -n final -o wide

#### Access the app via loadbalancer's URL through port 81

15. Delete EKS Cluster
   
   - eksctl delete cluster clo835 

16. Delete the remainder of you resources.
   
