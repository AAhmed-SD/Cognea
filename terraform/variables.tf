variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0c02fb55956c7d316" # Amazon Linux 2
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "repository_url" {
  description = "Git repository URL"
  type        = string
  default     = "https://github.com/your-username/cognie.git"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
} 