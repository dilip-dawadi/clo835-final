# CLO835 Proper Step-by-Step Commands

Run all commands from the repository root.

## 0) Set Variables

```bash
cd /Users/dilipdawadi/Developer/clo835-assignment1-app

export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=677868816391
export CLUSTER_NAME=clo835
export NAMESPACE=final
```

## 1) Check Tools

```bash
aws --version
kubectl version --client
eksctl version
docker --version
```

## 2) Show ECR Repositories

```bash
aws ecr describe-repositories --region "$AWS_REGION"
```

## 3) Show Github Actions for Docker Build and Push

Check .github/workflows/docker-ecr.yml for the build and push workflow. It should trigger on pushes to master and use the IMAGE_TAG variable for tagging the Docker image. Verify that the workflow is set up correctly in your GitHub repository under the Actions tab.

## 4) Create or Connect to EKS Cluster

Create new cluster:

```bash
eksctl create cluster -f eks-cluster.yaml
```

Or if it already exists:

```bash
aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
```

Verify nodes:

```bash
kubectl get nodes
```

## 5) Install and Verify EBS CSI (required for PVC)

```bash
eksctl create addon --name aws-ebs-csi-driver --cluster "$CLUSTER_NAME" --region "$AWS_REGION" --force
eksctl get addon --cluster "$CLUSTER_NAME" --region "$AWS_REGION"
kubectl get pods -n kube-system | grep -Ei "ebs|csi"
```

Note: In learner lab, you may see an OIDC warning. If addon status is Active and PVC binds, storage setup is good.

## 6) Ensure gp2 StorageClass Exists

Check storage classes:

```bash
kubectl get storageclass
```

If gp2 is missing, create it:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
parameters:
  type: gp2
  fsType: ext4
EOF
```

## 7) Deploy Application Manifests

```bash
kubectl apply -f clo835-manifests/namespace.yaml
kubectl apply -f clo835-manifests/configmap.yaml
kubectl apply -f clo835-manifests/secret.yaml
kubectl apply -f clo835-manifests/sa-irsa.yaml
kubectl apply -f clo835-manifests/rbac.yaml
kubectl apply -f clo835-manifests/pvc.yaml
kubectl apply -f clo835-manifests/mysql-deployment.yaml
kubectl apply -f clo835-manifests/mysql-service.yaml
kubectl apply -f clo835-manifests/app-deployment.yaml
kubectl apply -f clo835-manifests/app-service.yaml
kubectl apply -f clo835-manifests/hpa.yaml
```

## 8) Verify Everything

```bash
kubectl get ns
kubectl get all -n "$NAMESPACE"
kubectl get pvc -n "$NAMESPACE"
kubectl get pv
kubectl logs -n "$NAMESPACE" deploy/webapp --tail=100
```

Watch status in separate terminals:

```bash
kubectl get pods -n "$NAMESPACE" -w
```

```bash
kubectl get pvc -n "$NAMESPACE" -w
```

## 9) If MySQL Is Pending, Run This Fix Block

```bash
kubectl describe pvc mysql-pvc -n "$NAMESPACE"
kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp | tail -n 40
kubectl get storageclass
kubectl get pods -n kube-system | grep -Ei "ebs|csi"

kubectl delete pvc mysql-pvc -n "$NAMESPACE" --ignore-not-found
kubectl apply -f clo835-manifests/pvc.yaml
kubectl delete pod -n "$NAMESPACE" -l app=mysql --ignore-not-found
kubectl get pvc -n "$NAMESPACE" -w
```

## 10) Open Application

```bash
kubectl get svc webapp -n "$NAMESPACE"
```

Open EXTERNAL-IP in browser.

## 11) Verify Data Persistence

Insert test row:

```bash
kubectl exec -n "$NAMESPACE" deploy/mysql -- mysql -uroot -ppw -e "USE employees; INSERT INTO employee VALUES ('999','Test','User','K8s','Toronto'); SELECT * FROM employee WHERE emp_id='999';"
```

Delete mysql pod:

```bash
kubectl delete pod -n "$NAMESPACE" -l app=mysql
kubectl get pods -n "$NAMESPACE" -w
```

Re-check row after mysql pod is Running:

```bash
kubectl exec -n "$NAMESPACE" deploy/mysql -- mysql -uroot -ppw -e "USE employees; SELECT * FROM employee WHERE emp_id='999';"
```

## 12) Verify HPA Bonus

```bash
kubectl get hpa -n "$NAMESPACE"
```

Generate load:

```bash
kubectl run -n "$NAMESPACE" loadgen --rm -it --image=busybox -- /bin/sh -c "while true; do wget -q -O- http://webapp; done"
```

Watch scaling in another terminal:

```bash
kubectl get hpa -n "$NAMESPACE" -w
kubectl get pods -n "$NAMESPACE" -w
```

## 13) Change Background Image from ConfigMap

Edit BG_IMAGE_URL in clo835-manifests/configmap.yaml, then run:

```bash
kubectl apply -f clo835-manifests/configmap.yaml
kubectl rollout restart deployment/webapp -n "$NAMESPACE"
kubectl logs -n "$NAMESPACE" deploy/webapp --tail=100 | grep "Background image URL"
```

Refresh browser and verify the new image.

## 14) Cleanup (optional)

```bash
eksctl delete cluster --name "$CLUSTER_NAME" --region "$AWS_REGION"
```
