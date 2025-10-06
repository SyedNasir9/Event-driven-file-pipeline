variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "ap-south-1"
}

variable "account_id" {
  description = "Your AWS account ID"
  type        = string
}
