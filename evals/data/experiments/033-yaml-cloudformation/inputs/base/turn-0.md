Create an AWS CloudFormation template for a 3-tier web application.

Include:
- Parameters: environment, instance type, DB instance class, VPC CIDR
- VPC with 2 public and 2 private subnets, NAT Gateway, route tables
- Application Load Balancer with target group and listener
- Auto Scaling Group with launch template, scaling policies
- RDS PostgreSQL in private subnet with multi-AZ
- Security groups for ALB, EC2, and RDS
- Outputs: ALB DNS, RDS endpoint, VPC ID

Use section IDs: parameters, vpc-resources, compute, database, outputs

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.