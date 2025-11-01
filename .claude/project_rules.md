# Claude Code 项目规则

> 这些规则是Claude Code在本项目中必须遵守的核心准则

## 必须遵守的原则

### 1. 文档先行
- ✅ 每次修改前必须先阅读相关文档
- ✅ 所有设计决策必须在文档中体现
- ✅ 代码变更必须同步更新对应文档
- ✅ 文档路径参考: `docs/README.md`

### 2. 架构约束
- ❌ 禁止偏离 `docs/02_architecture/` 中的架构设计
- ❌ 禁止修改数据库schema（除非更新migration和文档）
- ❌ 禁止修改API端点签名（除非更新API文档）
- ⚠️ 如需修改架构，必须先在 `.claude/architecture_decisions.md` 中记录ADR

### 3. 测试要求
- ✅ 每个功能实现后必须编写测试
- ✅ 测试覆盖率必须 > 80%
- ✅ 所有测试必须通过才能提交
- ✅ 业务规则验证测试失败视为严重问题

### 4. 代码规范
- ✅ 遵循 `.claude/code_standards.md`
- ✅ 所有API必须符合OpenAPI规范
- ✅ 所有函数必须有docstring和类型注解
- ✅ 使用Black和isort格式化代码

### 5. 提交规范
- ✅ 每个commit只做一件事
- ✅ Commit message格式: `[模块名] 动作 + 简述`
- ✅ 示例: `[DataCollector] Add Redis caching for market data`
- ❌ 禁止提交未测试的代码

---

## 工作流程

### 标准开发流程
```
1. 阅读任务
   ↓
2. 查阅设计文档 (docs/02_architecture/ 和 docs/03_implementation/)
   ↓
3. 创建代码骨架（函数签名+docstring）
   ↓
4. 等待审查通过
   ↓
5. 实现功能代码
   ↓
6. 编写测试
   ↓
7. 运行测试确保通过
   ↓
8. 更新文档（如有必要）
   ↓
9. 标记任务完成（TodoWrite）
   ↓
10. 提交代码
```

### 每日工作结束流程
```
1. 运行 .claude/daily_checklist.md
   ↓
2. 更新 .claude/progress_tracker.md
   ↓
3. 执行偏离检测
   ↓
4. 提交代码并推送
```

---

## Claude必须询问的情况

在以下情况下，Claude **必须先问我**，不能自行决定：

### 技术决策
- [ ] 需要添加新的第三方依赖
- [ ] 需要修改数据库schema
- [ ] 需要改变API端点的签名
- [ ] 需要修改配置文件结构

### 架构决策
- [ ] 发现设计文档与需求矛盾
- [ ] 需要重构超过50行的代码
- [ ] 性能问题需要改变架构
- [ ] 需要添加新的模块或服务

### 问题和风险
- [ ] 测试失败且不确定原因
- [ ] 发现潜在的安全问题
- [ ] 遇到外部API限制或错误
- [ ] 性能指标未达标

### 询问格式模板

```markdown
⚠️ 需要你的决策：

**问题**: [清晰描述问题]

**背景**: [为什么会遇到这个问题]

**选项1**: [方案A]
- 优点: [列出优点]
- 缺点: [列出缺点]
- 影响: [对系统的影响]

**选项2**: [方案B]
- 优点: [列出优点]
- 缺点: [列出缺点]
- 影响: [对系统的影响]

**我的建议**: [推荐方案X]
**理由**: [为什么推荐这个方案]

**你的决定**？
```

---

## 禁止事项

### 绝对禁止 ❌
1. 跳过测试编写
2. 提交未通过测试的代码
3. 硬编码API密钥、密码等敏感信息
4. 修改生产数据库（使用测试网/测试数据库）
5. 添加未经讨论的第三方依赖
6. 偏离架构设计而不记录ADR
7. 删除或注释掉失败的测试

### 需要谨慎 ⚠️
1. 修改公共API接口（影响客户端）
2. 修改数据库schema（需要migration）
3. 重构大量代码（建议分步进行）
4. 使用实验性特性或beta版本库
5. 修改核心业务逻辑（需要详细测试）

---

## 代码质量标准

### 必须达到的指标
- ✅ 测试覆盖率 > 80%
- ✅ Pylint评分 > 8.0/10
- ✅ 无Black格式化错误
- ✅ 无明显的安全漏洞（Bandit扫描）

### 性能要求
- ✅ 数据采集 < 2秒
- ✅ AI决策 < 10秒
- ✅ 数据库查询 < 100ms
- ✅ API响应时间 < 500ms

### 文档要求
- ✅ 所有公共API有docstring
- ✅ 所有函数有类型注解
- ✅ 复杂逻辑有注释说明
- ✅ README包含使用示例

---

## 特定于本项目的规则

### NoF1.ai一致性要求
- ✅ AI调用频率必须是3分钟（不能更改）
- ✅ 技术指标计算必须与NoF1.ai一致（误差<0.1%）
- ✅ 提示词格式必须符合NoF1的11,053字符格式
- ✅ 交易的6个币种固定: BTC, ETH, SOL, BNB, DOGE, XRP

### 风险管理约束
- ✅ 单个币种仓位 ≤ 账户价值的20%
- ✅ 最大杠杆 ≤ 10x
- ✅ 最大回撤 ≤ 30%
- ✅ 每个仓位必须设置止损

### HyperLiquid集成要求
- ✅ 使用官方的hyperliquid-python-sdk
- ✅ 开发阶段使用测试网
- ✅ API请求必须有重试机制
- ✅ 处理API限流（60次/分钟）

---

## 版本控制规则

### Git Tag规则
- 每个Phase开始时打tag: `phase-X-start`
- 每个Phase完成时打tag: `phase-X-complete`
- Tag message必须包含完成的功能列表

### 分支策略
- `master`: 生产分支（稳定版本）
- `develop`: 开发分支（当前开发）
- `phase-X`: 阶段特性分支

### Commit Message规范
```
[模块名] 动作 + 简述

详细说明（可选）

关联issue: #123
```

**示例**:
```
[DataCollector] Add Redis caching for market data

- Implement cache layer with 180s TTL
- Add cache hit/miss metrics
- Handle cache failures gracefully

Closes #42
```

---

## 错误处理原则

### 必须处理的错误
- ✅ 网络请求失败（重试3次）
- ✅ API返回错误（记录并告警）
- ✅ 数据格式错误（验证并拒绝）
- ✅ 数据库操作失败（回滚事务）

### 错误处理模式
```python
# 好的错误处理
try:
    result = api_call()
except NetworkError as e:
    logger.error(f"Network error: {e}")
    # 重试逻辑
    retry(api_call, max_attempts=3)
except APIError as e:
    logger.error(f"API error: {e}")
    # 告警
    send_alert(e)
    raise
finally:
    # 清理资源
    cleanup()
```

### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 正常操作（如AI调用成功）
- `WARNING`: 异常情况但可恢复（如缓存未命中）
- `ERROR`: 错误需要关注（如API调用失败）
- `CRITICAL`: 严重错误需要立即处理（如超过最大回撤）

---

## 文档更新要求

### 何时更新文档

| 代码变更 | 必须更新的文档 |
|---------|--------------|
| 新增API端点 | `docs/02_architecture/api_design.md` |
| 修改数据库 | `docs/02_architecture/database_schema.md` + migration |
| 新增模块 | `docs/02_architecture/system_overview.md` |
| 修改配置 | `config.example.yaml` + `README.md` |
| 新增依赖 | `requirements.txt` + `docs/05_references/dependencies.md` |
| Bug修复 | `CHANGELOG.md` |
| 功能完成 | `.claude/progress_tracker.md` |

---

## 测试策略参考

参考 `.claude/testing_strategy.md` 了解：
- 单元测试要求
- 集成测试要求
- 业务规则验证要求
- 场景测试要求
- 性能测试要求

---

## 安全检查清单

- [ ] 无硬编码的密钥、密码、token
- [ ] 所有敏感配置使用环境变量
- [ ] 所有用户输入经过验证
- [ ] SQL查询使用参数化（防止注入）
- [ ] API端点有适当的认证/授权
- [ ] 错误信息不泄露敏感数据
- [ ] 日志不记录密码等敏感信息
- [ ] 使用HTTPS进行外部通信

---

## 参考资料

- **架构设计**: `docs/02_architecture/`
- **实施计划**: `docs/03_implementation/`
- **测试策略**: `.claude/testing_strategy.md`
- **代码规范**: `.claude/code_standards.md`
- **NoF1分析**: `docs/00_research/nof1_ai_analysis.md`
- **工程化指南**: `.dev/claude_code_workflow_guide.md` (仅本地)

---

## 最后提醒

> **记住**: 这些规则不是限制，而是确保项目质量和一致性的保障。
>
> 如果发现规则不合理或需要调整，请提出讨论，而不是默默违反。
>
> 质量 > 速度。宁可慢一点，也要做对。
