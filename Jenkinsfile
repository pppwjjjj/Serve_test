// Jenkinsfile —— ServeRest 自动化测试流水线（声明式）
//
// 流程：检出代码 → 启动 ServeRest → 测试容器跑全部用例（冒烟 → 正向 → 反向，
// 顺序由 pytest.ini 的 testpaths 保证）→ pytest-html 报告输出到 Allure_repo/
// → 归档报告 → 清理环境。
//
// 运行前提（Jenkins agent）：
// - 已安装 Docker 与 docker compose v2；
// - agent 为 Linux（示例使用 sh；Windows agent 需把 sh 换成 bat 并调整路径变量）。

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
                // 从干净状态开始：清掉上一轮遗留的容器
                sh 'docker compose down --remove-orphans || true'
                sh 'docker compose up -d --wait'
            }
        }

        stage('执行测试并生成报告') {
            steps {
                // 预建报告目录并放开权限：容器内 tests 以非 root 用户运行，
                // 绑定的宿主目录默认属主是 root，不放开会导致 pytest-html 写入失败。
                sh 'mkdir -p "$REPORT_DIR" && chmod -R 777 "$REPORT_DIR"'

                // tests 服务带 profile，需显式 --profile tests 才运行；
                // -v 把工作区 Allure_repo 挂载进容器，--html 指向挂载点，
                // 生成的单文件报告会落在 Jenkins 工作区。
                sh '''
                    docker compose --profile tests run --rm \
                      -v "${REPORT_DIR}:/app/reports" \
                      tests \
                      --html=/app/reports/pytest_report.html \
                      --self-contained-html \
                      -q
                '''
            }
        }
    }

    post {
        always {
            // 无论测试是否通过都清理环境，并归档报告（失败时 pytest-html 仍会生成报告）
            sh 'docker compose down --remove-orphans || true'
            archiveArtifacts artifacts: 'Allure_repo/pytest_report.html',
                fingerprint: true,
                allowMissingArchive: true

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
