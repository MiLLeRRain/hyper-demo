# 项目文档导航

> 本项目的所有文档索引

## 文档结构

```
docs/
├── 00_research/              # 研究与分析
├── 01_requirements/          # 需求文档
├── 02_architecture/          # 架构设计
├── 03_implementation/        # 实施计划
├── 04_testing/               # 测试文档
└── 05_references/            # 参考资料
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

- **user_stories.md**: 用户故事 (TODO)
- **functional_requirements.md**: 功能需求规格 (TODO)

---

## 02_architecture/ - 架构设计

系统架构和技术设计

- **system_overview.md**: 系统总览和架构图 (TODO)
- **api_design.md**: REST API设计 (TODO)
- **database_schema.md**: 数据库设计 (TODO)
- **data_flow.md**: 数据流设计 (TODO)

---

## 03_implementation/ - 实施计划

分阶段实施计划

- **phase_1_data_collection.md**: 阶段1 - 数据采集 (TODO)
- **phase_2_ai_integration.md**: 阶段2 - AI集成 (TODO)
- **phase_3_trading_execution.md**: 阶段3 - 交易执行 (TODO)
- **phase_4_automation.md**: 阶段4 - 自动化 (TODO)
- **phase_5_web_frontend.md**: 阶段5 - Web前端 (TODO)

---

## 04_testing/ - 测试文档

测试计划和测试用例

- **test_plan.md**: 测试计划 (TODO)
- **test_cases.md**: 测试用例 (TODO)
- **acceptance_tests.md**: 验收测试场景 (TODO)

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

## 其他重要文档

### 项目根目录
- **README.md**: 项目总览和快速开始
- **ROADMAP.md**: 项目路线图
- **CHANGELOG.md**: 变更日志 (TODO)

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
2. **开发中**: 参考 `02_architecture/` 和 `03_implementation/`
3. **测试时**: 参考 `04_testing/` 和 `.claude/testing_strategy.md`
4. **遇到问题**: 查看 `.claude/progress_tracker.md` 的问题记录

### 对于Claude Code
1. **每次任务开始**: 阅读相关的设计文档
2. **开发过程**: 遵循 `.claude/project_rules.md`
3. **每日结束**: 执行 `.claude/daily_checklist.md`
4. **记录进度**: 更新 `.claude/progress_tracker.md`

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
| ROADMAP.md | ✅ 完成 | 2025-11-01 |
| user_stories.md | ⏳ TODO | - |
| system_overview.md | ⏳ TODO | - |
| ... | ⏳ TODO | - |

---

## 快速链接

- [NoF1.ai分析](00_research/nof1_ai_analysis.md)
- [项目路线图](../ROADMAP.md)
- [项目规则](.claude/project_rules.md)
- [工程化指南](../.dev/claude_code_workflow_guide.md) (仅本地)
