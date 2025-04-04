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
  execution_role_arn = aws_iam_role.execution_role_arn.arn 
  task_role_arn = aws_iam_role.task_role_arn.arn
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu    = 1024
  memory = 4096
  container_definitions = jsonencode([
    {
      name      = "first",
      image     = "061051226319.dkr.ecr.us-east-1.amazonaws.com/agnesw-project:0.0.3",
      memory        = 4096
      cpu           = 1024
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group = aws_cloudwatch_log_group.agnesw_app_task_log.name
          awslogs-region = "us-east-1"
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = [
        { name = "INPUT_DIR", value = "/data/input"},
        { name = "OUTPUT_DIR", value = "/data/output"},
        { name = "S3_BUCKET_NAME", value = "agnesw-project"},
        { name = "RUN_MODE", value = "aws"},
        { name = "OUTPUT_S3_KEY", value = "output/aiml_info.csv"}
      ],
    }
  ])
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

resource "aws_cloudwatch_log_group" "agnesw_app_task_log" {
  name = "/ecs/agnesw_app_task_log"
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
