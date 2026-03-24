packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.8"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "region" {
  type    = string
  default = "ap-southeast-1"
}
variable "vpc_id" {
  type    = string
}

variable "subnet_id" {
  type    = string
}

source "amazon-ebs" "ubuntu" {
  ami_name      = "edutrust-base-ami-{{timestamp}}"
  instance_type = "t3.micro"
  region        = var.region
  ssh_username  = "ubuntu"

  vpc_id        = var.vpc_id
  subnet_id     = var.subnet_id

  associate_public_ip_address = true
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"] # Canonical
  }

  tags = {
    Name = "EduTrust-Base-AMI"
    OS   = "Ubuntu 24.04"
  }
}

build {
  name    = "edutrust-base-ami"
  sources = ["source.amazon-ebs.ubuntu"]

  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "cloud-init status --wait",
      
      "sudo apt-get update -y",
      "sleep 10",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl jq unzip",
      
      "echo 'Installing Docker...'",
      "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh",
      "sudo sh /tmp/get-docker.sh",
      "sudo systemctl enable --now docker",
      "sudo usermod -aG docker ubuntu",
      
      "echo 'Installing AWS CLI v2...'",
      "curl \"https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip\" -o \"awscliv2.zip\"",
      "unzip awscliv2.zip",
      "sudo ./aws/install",
      "rm -rf awscliv2.zip aws/"
    ]
  }
}
