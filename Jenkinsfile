// ServeRest 自动化测试流水线
//
// 适用环境：Windows + Docker Desktop（docker compose v2）
//
// Jenkins 一次性配置（与仓库无关，需在 Jenkins 界面完成）：
//   1. 安装插件：Allure Jenkins Plugin
//   2. Manage Jenkins → Tools → Allure Commandline → 自动安装
//   3. 新建 Pipeline 任务，SCM 指向本仓库，Script Path 填 Jenkinsfile
//
// 流程：构建镜像 → 启动 ServeRest → 冒烟 → 全量用例并生成报告数据 → 发布报告

pipeline {
    agent any

    triggers {
        // 无 webhook 时每 5 分钟检查一次远端新提交
        pollSCM('H/5 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Build Image') {
            steps {
                // tests 服务带 profile，构建时需显式启用
                bat 'docker compose --profile tests build'
            }
        }

        stage('Start ServeRest') {
            steps {
                bat 'docker compose down --remove-orphans || exit /b 0'
                bat 'docker compose up -d --wait'
            }
        }

        stage('Smoke Tests') {
            steps {
                // 冒烟只做连通性门禁，不产出报告数据
                bat 'docker compose --profile tests run --rm tests -m smoke -q'
            }
        }

        stage('Full Test Suite') {
            steps {
                // 清空上一轮报告，避免结果累积
                bat 'if exist Allure_repo rmdir /s /q Allure_repo'
                bat 'mkdir Allure_repo\\allure-results'

                // 放开挂载目录 ACL，容器内非 root 用户才可写入（失败仅告警）
                bat 'icacls "%cd%\\Allure_repo" /grant *S-1-1-0:(OI)(CI)F /T /Q >nul 2>&1 || exit /b 0'

                // 全量用例（冒烟 → 正向 → 反向，顺序由 pytest.ini testpaths 保证），
                // 产出 Allure 原始结果
                bat 'docker compose --profile tests run --rm -v "%cd%\\Allure_repo:/app/reports" tests -q --alluredir=/app/reports/allure-results'
            }
        }

        stage('Publish Reports') {
            steps {
                // 构建页会出现 Allure Report 链接
                allure([
                    includeProperties: false,
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: 'Allure_repo/allure-results']]
                ])

            }
        }
    }

    post {
        always {
            // 无论成败都清理容器环境
            bat 'docker compose down --remove-orphans || exit /b 0'
        }
    }
}
