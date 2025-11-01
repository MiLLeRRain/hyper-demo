# 每日工作结束检查清单

> 每天工作结束前必须完成的检查项

## 使用方法

在每天工作结束前，Claude应该：
1. 阅读此清单
2. 逐项检查并运行相应命令
3. 生成检查报告
4. 标注所有未通过的项

---

## 代码质量 ✅

- [ ] **所有新代码有单元测试**
  - 检查命令: `pytest tests/unit/ -v --cov=backend --cov-report=term-missing`
  - 要求: 新增代码必须有对应测试

- [ ] **测试通过率 100%**
  - 检查命令: `pytest tests/ -v`
  - 要求: 所有测试必须通过，不允许跳过

- [ ] **代码覆盖率 > 80%**
  - 检查命令: `pytest --cov=backend --cov-report=term`
  - 要求: 整体覆盖率必须大于80%

- [ ] **没有TODO或FIXME注释留存**
  - 检查命令: `grep -r "TODO\|FIXME" backend/ --exclude-dir=__pycache__`
  - 要求: 所有TODO必须处理或转换为Issue

- [ ] **代码已格式化**
  - 检查命令: `black --check backend/` 和 `isort --check backend/`
  - 要求: 无格式化错误

- [ ] **无明显的代码质量问题**
  - 检查命令: `pylint backend/ --disable=C0103,C0114 --fail-under=8.0`
  - 要求: Pylint评分 > 8.0

---

## 架构一致性 🏗️

- [ ] **未偏离设计文档**
  - 检查方式: 对比实际代码与 `docs/02_architecture/`
  - 要求: 任何偏离必须记录在 `.claude/architecture_decisions.md`

- [ ] **所有API符合 api_design.md**
  - 检查方式: 对比API实现与文档
  - 要求: API端点、参数、返回值必须一致

- [ ] **数据库变更已记录migration**
  - 检查命令: `alembic history` (如果使用Alembic)
  - 要求: 所有schema变更必须有migration文件

- [ ] **新增依赖已记录**
  - 检查命令: `git diff requirements.txt`
  - 要求: 新依赖必须在requirements.txt中

---

## 文档 📚

- [ ] **更新了 .claude/progress_tracker.md**
  - 内容:
    - 今天完成的任务（含文件路径和commit hash）
    - 进行中任务的进度百分比
    - 遇到的问题
    - 架构偏离（如有）

- [ ] **更新了相关模块文档**
  - 要求: 如果修改了接口，必须更新 `docs/02_architecture/`

- [ ] **更新了 CHANGELOG.md**
  - 要求: 记录所有用户可见的变更

- [ ] **API文档自动生成无错误**
  - 检查命令: 生成OpenAPI/Swagger文档
  - 要求: 文档生成成功且无错误

---

## Git 🔧

- [ ] **Commit message 符合规范**
  - 格式: `[模块名] 动作 + 简述`
  - 示例: `[DataCollector] Add Redis caching for market data`

- [ ] **已推送到远程仓库**
  - 检查命令: `git status` 显示 "Your branch is up to date"
  - 要求: 所有commit已推送

- [ ] **没有未跟踪的文件（除了临时文件）**
  - 检查命令: `git status` 查看 Untracked files
  - 要求: 所有应该追踪的文件已add

- [ ] **没有大文件(>1MB)被提交**
  - 检查命令: `git ls-files -s | awk '{if($4 > 1000000) print $4, $5}'`
  - 要求: 大文件应使用Git LFS或排除

---

## 测试 🧪

- [ ] **单元测试通过**
  - 检查命令: `pytest tests/unit/ -v`
  - 要求: 100%通过

- [ ] **集成测试通过（如果有）**
  - 检查命令: `pytest tests/integration/ -v`
  - 要求: 100%通过

- [ ] **业务规则验证通过**
  - 检查命令: `pytest tests/business_rules/ -v`
  - 要求: 100%通过（这是关键）

- [ ] **场景测试通过（如果该模块完成）**
  - 检查命令: `pytest tests/scenarios/ -v`
  - 要求: 100%通过

---

## 性能 ⚡

- [ ] **关键路径性能符合要求**
  - 数据采集: < 2秒
  - AI决策: < 10秒
  - 交易执行: < 1秒
  - 检查方式: 运行性能测试或查看日志

- [ ] **无明显的性能问题**
  - 检查方式: 查看日志中的慢查询告警
  - 要求: 数据库查询 < 100ms

---

## 安全 🔒

- [ ] **无硬编码的密钥或密码**
  - 检查命令: `grep -r "api_key\|password\|secret\|token" backend/ --include="*.py"`
  - 要求: 敏感信息必须使用环境变量

- [ ] **敏感配置使用环境变量**
  - 检查方式: 审查 `config.yaml` 和 `.env.example`
  - 要求: 无明文密钥

- [ ] **输入验证完整**
  - 检查方式: Review API端点的参数验证
  - 要求: 所有用户输入必须验证

---

## 可选检查（重要功能）⭐

- [ ] **日志输出合理（不过多不过少）**
  - 检查方式: 运行系统查看日志
  - 要求: DEBUG用于调试，INFO用于关键操作，ERROR/CRITICAL用于异常

- [ ] **错误处理覆盖所有预期异常**
  - 检查方式: Review所有try-except块
  - 要求: 具体异常处理，避免捕获所有Exception

- [ ] **资源清理正确（连接、文件句柄）**
  - 检查方式: 审查是否使用with语句或finally
  - 要求: 数据库连接、文件、网络请求正确关闭

---

## 检查报告模板

```markdown
## 每日检查报告 (YYYY-MM-DD)

### ✅ 通过项 (X/Y)
- 代码质量: [具体数量]
- 架构一致性: [具体数量]
- Git: [具体数量]
...

### ⚠️ 警告项 (X)
1. [项目名称]
   - 问题: [描述]
   - 建议: [改进建议]

### ❌ 失败项 (X)
1. [项目名称]
   - 错误: [详细错误信息]
   - 影响: [影响范围]
   - 优先级: [高/中/低]
   - 建议: [修复建议]

### 建议
- [具体建议1]
- [具体建议2]
```

---

## 使用说明

### 对于Claude
每天工作结束前，运行：
```
请执行每日检查清单：
1. 阅读 .claude/daily_checklist.md
2. 逐项检查，运行相应的命令
3. 列出所有未通过的项，并说明原因
4. 如果有重要问题（如测试失败），暂停并告诉我
5. 生成一份检查报告
```

### 对于开发者
- 每天工作结束前，让Claude执行此清单
- 审查Claude生成的报告
- 决定哪些问题需要立即修复
- 哪些可以记录为技术债务

---

## 常见问题

### Q: 测试覆盖率不足80%怎么办？
A:
1. 识别未覆盖的代码
2. 补充测试用例
3. 如果是不可测试的代码（如__init__.py），添加到豁免列表

### Q: Pylint评分低于8.0怎么办？
A:
1. 查看具体的问题
2. 修复重要的问题（E和W级别）
3. C级别（Convention）可以适当忽略
4. 可以在.pylintrc中配置豁免

### Q: 发现架构偏离怎么办？
A:
1. 立即停止开发
2. 在 .claude/architecture_decisions.md 中记录ADR
3. 讨论是否接受这个偏离
4. 如果接受，更新架构文档
5. 如果不接受，回退代码
