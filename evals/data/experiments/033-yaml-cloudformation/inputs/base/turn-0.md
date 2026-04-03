Create an AWS CloudFormation template for a 3-tier web application.

Include:
- Parameters: environment, instance type, DB instance class, VPC CIDR
- VPC with 2 public and 2 private subnets, NAT Gateway, route tables
- Application Load Balancer with target group and listener
- Auto Scaling Group with launch template, scaling policies
- RDS PostgreSQL in private subnet with multi-AZ
- Security groups for ALB, EC2, and RDS
- Outputs: ALB DNS, RDS endpoint, VPC ID
