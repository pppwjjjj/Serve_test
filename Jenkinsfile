// Jenkinsfile —— ServeRest 自动化测试流水线（声明式，Windows agent 版）
//
// 流程：检出代码 → 启动 ServeRest → 测试容器跑全部用例（冒烟 → 正向 → 反向，
// 顺序由 pytest.ini 的 testpaths 保证）→ pytest-html 报告输出到 Allure_repo/
// → 归档报告 → 清理环境。
//
// 运行前提（本机 Windows + Docker Desktop）：
// - Docker 与 docker compose v2 可用（jenkins 服务/进程的运行账号能调到 docker）；
// - 本文件全部使用 bat（cmd）步骤，无需 Linux shell。

pipeline {
    agent any

    triggers {
        // 自动构建：推荐在 Jenkins 里给仓库配 GitHub webhook（推送即触发）；
        // pollSCM 是没配 webhook 时的兜底，每 5 分钟检查一次远端是否有新提交。
        pollSCM('H/5 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        // 报告输出目录：Jenkins 工作区（仓库检出目录）下的 Allure_repo
        REPORT_DIR = "${WORKSPACE}/Allure_repo"
    }

    stages {
        stage('启动 ServeRest') {
            steps {
                // 从干净状态开始：清掉上一轮遗留的容器（失败也继续）
                bat 'docker compose down --remove-orphans || exit /b 0'
                bat 'docker compose up -d --wait'
            }
        }

        stage('执行测试并生成报告') {
            steps {
                // 预建报告目录（%REPORT_DIR% 来自 environment 块）
                bat 'if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"'

                // Docker Desktop 的 bind mount 由容器内非 root 用户写入时，
                // 放开宿主机目录 ACL（Everyone 完全控制），失败仅告警不中断。
                // 注意：cmd 里的 % 本身要写成 %%，SID 写法会被转义，这里改用通配：
                bat 'icacls "%REPORT_DIR%" /grant *S-1-1-0:(OI)(CI)F /T /Q >nul 2>&1 || exit /b 0'

                // tests 服务带 profile，需显式 --profile tests 才运行；
                // -v 把工作区 Allure_repo 挂载进容器，报告落在 Jenkins 工作区。
                bat 'docker compose --profile tests run --rm -v "%REPORT_DIR%:/app/reports" tests --html=/app/reports/pytest_report.html --self-contained-html -q'
            }
        }
    }

    post {
        always {
            // 无论测试是否通过都清理环境（失败也继续，保证归档/发布报告能执行）
            bat 'docker compose down --remove-orphans || exit /b 0'

            // 归档报告（失败时 pytest-html 仍会生成报告；没生成也不报错）
            archiveArtifacts artifacts: 'Allure_repo/pytest_report.html',
                fingerprint: true,
                allowEmptyArchive: true

            // 在 Jenkins 构建页面发布图形化报告（需要安装 HTML Publisher 插件）。
            // 插件缺失时只打印提示，不影响构建结果。
            script {
                try {
                    publishHTML(target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'Allure_repo',
                        reportFiles: 'pytest_report.html',
                        reportName: 'ServeRest 测试报告'
                    ])
                } catch (Exception e) {
                    echo "未安装 HTML Publisher 插件，跳过报告发布（报告仍已归档）：${e}"
                }
            }
        }
    }
}
