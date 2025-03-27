resource "aws_s3_bucket" "agnesw-project" {
  bucket = "agnesw-project"

  tags = {
    Owner = element(split("/", data.aws_caller_identity.current.arn), 1)
  }
}

resource "aws_s3_bucket_ownership_controls" "agnesw-project_ownership_controls" {
  bucket = aws_s3_bucket.agnesw-project.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "agnesw-project_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.agnesw-project_ownership_controls]

  bucket = aws_s3_bucket.agnesw-project.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "agnesw-project_expiration" {
  bucket = aws_s3_bucket.agnesw-project.id

  rule {
    id      = "compliance-retention-policy"
    status  = "Enabled"

    expiration {
	  days = 100
    }
  }
}

resource "aws_ecr_repository" "agnesw-project" {
  name                 = "agnesw-project"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecs_task_definition" "service" {
  family = "agnesw_app"
  container_definitions = jsonencode([
    {
      name      = "first"
      image     = "061051226319.dkr.ecr.us-east-1.amazonaws.com/agnesw-project:0.0.1"
      cpu       = 256
      memory    = 2048
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
    },
    {
      name      = "second"
      image     = "061051226319.dkr.ecr.us-east-1.amazonaws.com/agnesw-project:0.0.1"
      cpu       = 128
      memory    = 256
      essential = true
      portMappings = [
        {
          containerPort = 443
          hostPort      = 443
        }
      ]
    }
  ])

  volume {
    name      = "service-storage"
    host_path = "/ecs/service-storage"
  }

  placement_constraints {
    type       = "memberOf"
    expression = "attribute:ecs.availability-zone in [us-east-1a, us-east-1b]"
  }
}

resource "aws_iam_role" "execution_role_arn" {
  name = "agnesw_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.execution_role_arn.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task_role_arn" {
  name = "agnesw_task_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "ecs_task_custom_policy" {
  name        = "ecsTaskCustomPolicy"
  description = "Policy for ECS task to access S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket", "s3:PutObject"]
        Resource = [
          "arn:aws:s3:::agnesw-project",
          "arn:aws:s3:::agnesw-project/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_role_arn_attachment" {
  role       = aws_iam_role.task_role_arn.name
  policy_arn = aws_iam_policy.ecs_task_custom_policy.arn
}
