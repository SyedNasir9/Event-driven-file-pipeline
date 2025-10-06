output "eks_instance_profile_name" {
  value = aws_iam_instance_profile.eks_nodes_profile.name
}

output "eks_node_role_arn" {
  value = aws_iam_role.eks_nodes_role.arn
}

output "eks_cluster_role_arn" {
  value = aws_iam_role.eks_cluster_role.arn
}
