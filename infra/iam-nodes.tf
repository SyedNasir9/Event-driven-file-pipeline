# IAM Policy for S3, SQS, DynamoDB access for nodes/pods
data "aws_iam_policy_document" "node_policy_doc" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "k8s_nodes_policy" {
  name   = "k8s-event-pipeline-node-policy"
  policy = data.aws_iam_policy_document.node_policy_doc.json
}

# Node IAM Role
data "aws_iam_policy_document" "eks_node_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_nodes_role" {
  name               = "k8s-event-pipeline-eks-nodes-role"
  assume_role_policy = data.aws_iam_policy_document.eks_node_assume_role.json
}

resource "aws_iam_role_policy_attachment" "attach_node_policy" {
  role       = aws_iam_role.eks_nodes_role.name
  policy_arn = aws_iam_policy.k8s_nodes_policy.arn
}

resource "aws_iam_instance_profile" "eks_nodes_profile" {
  name = "k8s-event-pipeline-eks-node-profile"
  role = aws_iam_role.eks_nodes_role.name
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  role       = aws_iam_role.eks_nodes_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  role       = aws_iam_role.eks_nodes_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "ec2_registry_readonly" {
  role       = aws_iam_role.eks_nodes_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

