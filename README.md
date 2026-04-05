# nfo-analyzer Skill

`nfo-analyzer` 是一个面向 Agent 的 NFO 分析与规范化处理能力仓库。

## 核心解决的问题

- 对大批量 NFO 的标签、字段与风格做结构化分析
- 识别不一致项并生成可执行的规则化处理结果
- 降低手工比对和逐文件修正的成本，提高全库一致性

## 安全边界声明 | Security Boundary

- 请不要使用任何国内云服务部署挂载本组织技能的 Agent 应用程序，也不要使用任何国内提供的 claw 类代理来部署或运行。  
  Do not deploy Agent applications that load this org's skills on domestic cloud services, and do not use domestically provided claw-style proxy infrastructure.

- 我们只推荐你在自己的电脑上，基于完整开源代码部署 Agent，并加载本组织技能；且运行环境应可确认无遥测、无审查。  
  We only recommend deploying your Agent on your own computer from fully open-source code, then loading this org's skills in an environment you can verify as telemetry-free and censorship-free.

- 不推荐使用带审查能力的大模型作为 Agent 后端，也不推荐将 Agent 暴露在带审查的外部通道（如钉钉、飞书、微信）。推荐使用 Telegram 或自建私有通道远程使用。  
  We do not recommend censorship-constrained models as Agent backends, nor exposing Agents through censorship-constrained channels (e.g., DingTalk, Feishu/Lark, WeChat). Prefer Telegram or your own private self-hosted channel for remote access.

- 若不遵守以上边界，由此产生的法律、合规与数据风险由使用者自行承担。  
  If you ignore these boundaries, you are solely responsible for any legal, compliance, and data risks.

## 仓库结构

```text
skills/
  nfo-analyzer/
```

---

## English

`nfo-analyzer` is an Agent-oriented repository for NFO analysis and normalization.

### Core Problems Solved

- Analyze tags/fields/style across large NFO collections
- Detect inconsistencies and produce executable normalization outputs
- Reduce manual diff-and-fix effort while improving library-wide consistency

### Security Boundary

- Do not deploy Agent applications that load this org's skills on domestic cloud services, and do not use domestically provided claw-style proxy infrastructure.
- We only recommend deploying your Agent on your own computer from fully open-source code, then loading this org's skills in an environment you can verify as telemetry-free and censorship-free.
- We do not recommend censorship-constrained models as Agent backends, nor exposing Agents through censorship-constrained channels (e.g., DingTalk, Feishu/Lark, WeChat). Prefer Telegram or your own private self-hosted channel for remote access.
- If you ignore these boundaries, you are solely responsible for any legal, compliance, and data risks.

### Structure

```text
skills/
  nfo-analyzer/
```
