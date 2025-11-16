# 项目文档导航

> Trading Bot 项目的完整文档索引

## 文档结构

```
docs/
├── 00_research/              # 研究与分析
├── 01_requirements/          # 需求文档
├── 02_architecture/          # 架构设计
├── 03_implementation/        # 实施计划
├── 04_testing/               # 测试文档
├── 05_references/            # 参考资料
├── 06_deployment/            # 部署文档
└── 07_operations/            # 运维文档
```

---

## 00_research/ - 研究与分析

研究NoF1.ai和相关技术的文档

- **nof1_ai_analysis.md**: NoF1.ai网站完整分析
- **nof1_ai_system_prompts_and_outputs.md**: NoF1.ai的AI提示词和输出
- **implementation_approaches.md**: 实现方案对比

---

## 01_requirements/ - 需求文档

系统需求和用户故事

- **user_stories.md**: 用户故事
- **functional_requirements.md**: 功能需求规格

---

## 02_architecture/ - 架构设计

系统架构和技术设计

- **system_overview.md**: 系统总览和架构图
- **api_design.md**: REST API设计
- **database_schema.md**: 数据库设计 ✅ 已更新
- **data_flow.md**: 数据流设计
- **project_structure.md**: 项目结构说明 ✅ 新增

---

## 03_implementation/ - 实施计划

分阶段实施计划和实现指南

### 阶段计划
- **phase_1_data_collection.md**: 阶段1 - 数据采集
- **phase_2_ai_integration.md**: 阶段2 - AI集成
- **phase_3_trading_execution.md**: 阶段3 - 交易执行
- **phase_4_automation.md**: 阶段4 - 自动化
- **phase_5_web_frontend.md**: 阶段5 - Web前端

### 实现指南
- **agent_configuration.md**: 多Agent配置指南 ✅ 新增
- **multi_agent_setup.md**: 多Agent系统设置 ✅ 新增
- **strategy_design.md**: 策略设计指南 ✅ 新增
- **temperature_guide.md**: LLM温度参数分析 ✅ 新增
- **llm_integration.md**: LLM集成指南 ✅ 新增

---

## 04_testing/ - 测试文档

测试计划和测试用例

- **test_plan.md**: 测试计划
- **integration_test_setup_guide.md**: 集成测试准备指南
- **testnet_setup.md**: 测试网设置完整指南 ✅ 新增
- **testnet_quick_start.md**: 测试网快速开始 ✅ 新增
- **mainnet_testing.md**: 主网测试指南 ✅ 新增
- **integration_testing.md**: 集成测试文档 ✅ 新增

---

## 05_references/ - 参考资料

外部参考资料和技术文档

### hyperliquid/
- **api_data_availability_CN.md**: HyperLiquid数据可用性
- **margin_and_fees_CN.md**: HyperLiquid保证金和费用
- **trading_api_guide_CN.md**: HyperLiquid交易API指南

### llm/
- **provider_guide.md**: LLM提供商选择指南
- **cost_calculator.md**: LLM成本计算器
- **deepseek_model_comparison.md**: DeepSeek模型对比

---

## 06_deployment/ - 部署文档

数据库和系统部署指南

- **database_setup.md**: PostgreSQL数据库安装配置 ✅ 新增
- **database_schema_reference.md**: 数据库Schema参考 ✅ 新增
- **environment_switching.md**: 环境切换指南 ✅ 新增
- **long_term_running_guide.md**: 长期运行完整指南 ✅ 新增
- **long_term_running_summary.md**: 长期运行快速总结 ✅ 新增

---

## 07_operations/ - 运维文档

日常运维和项目管理

- **commands.md**: 常用命令参考 ✅ 新增
- **roadmap.md**: 项目路线图 ✅ 新增

---

## 其他重要文档

### 项目根目录
- **README.md**: 项目总览和快速开始
- **.env.example**: 环境变量配置示例

### .claude/ (项目规范)
- **project_rules.md**: Claude Code必须遵守的项目规则
- **code_standards.md**: 代码规范
- **testing_strategy.md**: 测试策略
- **architecture_decisions.md**: 架构决策记录(ADR)
- **progress_tracker.md**: 进度追踪
- **daily_checklist.md**: 每日检查清单

### .dev/ (仅本地，不提交Git)
- **claude_code_workflow_guide.md**: 使用Claude Code的完整工程化管理方法

---

## 文档使用指南

### 对于开发者
1. **开始前**: 阅读 `README.md` 和 `.claude/project_rules.md`
2. **环境配置**: 参考 `06_deployment/` 配置数据库和环境
3. **开发中**: 参考 `02_architecture/` 和 `03_implementation/`
4. **测试时**: 参考 `04_testing/` 进行测试网和主网测试
5. **遇到问题**: 查看 `.claude/progress_tracker.md` 的问题记录

### 对于Claude Code
1. **每次任务开始**: 阅读相关的设计文档
2. **开发过程**: 遵循 `.claude/project_rules.md`
3. **每日结束**: 执行 `.claude/daily_checklist.md`
4. **记录进度**: 更新 `.claude/progress_tracker.md`

---

## 快速开始流程

### 1. 环境配置
```bash
# 1. 克隆项目
git clone <repository>
cd hyper-demo

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的API密钥

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置数据库
# 参考: docs/06_deployment/database_setup.md
python scripts/init_database.py --sample-data
```

### 2. 测试网测试
```bash
# 参考: docs/04_testing/testnet_quick_start.md
python test_testnet_connection.py
python test_testnet_trading.py
```

### 3. 运行机器人
```bash
# 参考: docs/07_operations/commands.md
python tradingbot.py start
```

---

## 文档更新规则

### 何时更新文档

| 代码变更 | 必须更新的文档 |
|---------|--------------|
| 新增API端点 | `02_architecture/api_design.md` |
| 修改数据库 | `02_architecture/database_schema.md` |
| 新增模块 | `02_architecture/system_overview.md` |
| 完成功能 | `.claude/progress_tracker.md` |
| Bug修复 | `CHANGELOG.md` |
| 新增配置 | `06_deployment/` 相关文档 |
| 新增测试 | `04_testing/` 相关文档 |

### 文档审查
- 每个Phase完成后，审查所有相关文档
- 确保文档与代码一致
- 记录任何架构偏离

---

## 文档状态

| 文档 | 状态 | 最后更新 |
|------|------|---------|
| nof1_ai_analysis.md | ✅ 完成 | 2025-10-30 |
| implementation_approaches.md | ✅ 完成 | 2025-10-30 |
| database_schema.md | ✅ 完成 | 2025-11-16 |
| database_setup.md | ✅ 完成 | 2025-11-16 |
| testnet_setup.md | ✅ 完成 | 2025-11-16 |
| agent_configuration.md | ✅ 完成 | 2025-11-16 |
| roadmap.md | ✅ 完成 | 2025-11-01 |
| user_stories.md | ✅ 完成 | 2025-11-01 |
| system_overview.md | ✅ 完成 | 2025-11-01 |

---

## 快速链接

### 研究与规划
- [NoF1.ai分析](00_research/nof1_ai_analysis.md)
- [项目路线图](07_operations/roadmap.md)
- [实现方案对比](00_research/implementation_approaches.md)

### 开发指南
- [系统架构](02_architecture/system_overview.md)
- [数据库设计](02_architecture/database_schema.md)
- [项目结构](02_architecture/project_structure.md)
- [LLM集成指南](03_implementation/llm_integration.md)
- [多Agent配置](03_implementation/agent_configuration.md)

### 部署与测试
- [数据库设置](06_deployment/database_setup.md)
- [测试网快速开始](04_testing/testnet_quick_start.md)
- [主网测试指南](04_testing/mainnet_testing.md)
- [环境切换](06_deployment/environment_switching.md)

### 运维管理
- [常用命令](07_operations/commands.md)
- [长期运行指南](06_deployment/long_term_running_guide.md)
- [项目规则](.claude/project_rules.md)
