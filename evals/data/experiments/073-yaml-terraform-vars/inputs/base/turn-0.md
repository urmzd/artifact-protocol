Create a Terraform variables file in YAML format for an AWS infrastructure deployment.

Include:
- Environment settings: name, region, account ID, tags
- Networking: VPC CIDR, subnet CIDRs (public/private), availability zones, NAT gateway toggle
- Compute: instance types, AMI IDs, key pair name, auto-scaling min/max/desired
- Database: engine, version, instance class, storage, backup retention
- Monitoring: CloudWatch alarms, SNS topic ARNs, log retention days
