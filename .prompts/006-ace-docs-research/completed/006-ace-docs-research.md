# ACE Framework Deep Documentation Research

<session_initialization>
Before beginning research, verify today's date:
!`date +%Y-%m-%d`

Use this date when searching for "current" or "latest" information.
</session_initialization>

<research_objective>
Research the ACE (Agentic Context Engineering) Framework comprehensively to understand every aspect of its architecture, implementation, and capabilities.

Purpose: Enable proper integration of ACE learning capabilities into RALPH orchestrator
Scope: All ACE documentation, guides, examples, source code patterns
Output: ace-docs-research.md with complete framework understanding
</research_objective>

<research_scope>
<include>
**Core Architecture:**
- ACE framework philosophy and design principles
- Component architecture (Reflector, Skillbook, LiteLLM integration)
- Learning loop mechanics (inject → execute → learn cycle)
- Skill extraction and curation algorithms
- Confidence scoring and skill validation

**Configuration & Customization:**
- All configuration options and their effects
- Model selection and provider configuration
- Skillbook persistence formats and strategies
- Async vs sync learning modes
- Custom reflection prompts

**Integration Patterns:**
- Claude Code integration (primary reference)
- Generic agent integration patterns
- Subprocess management patterns
- Output parsing strategies
- Error handling and recovery

**Best Practices:**
- Optimal skill granularity
- When to trigger learning
- Skillbook maintenance (pruning, merging)
- Performance optimization
- Resource management

**Source Code Analysis:**
- Core classes and their responsibilities
- Public API surface
- Extension points
- Threading/async patterns
</include>

<exclude>
- RALPH-specific implementation (separate research)
- Benchmark design (planning phase)
- Alternative frameworks comparison (not needed)
</exclude>

<sources>
**Primary - Official Repository (USE repomix or WebFetch):**
- https://github.com/kayba-ai/agentic-context-engine (full repo)
- docs/COMPLETE_GUIDE_TO_ACE.md
- docs/INTEGRATION_GUIDE.md
- examples/claude-code-loop/
- ace/core/ (source code)
- ace/integrations/ (integration patterns)

**Context7 MCP:**
- Use mcp__Context7__resolve-library-id for "agentic-context-engine"
- Use mcp__Context7__get-library-docs for API patterns

**Search Queries (WebSearch):**
- "agentic context engine ACE framework 2025"
- "ACE framework agent learning loop"
- "ACE skillbook implementation"
</sources>
</research_scope>

<verification_checklist>
□ Read and document COMPLETE_GUIDE_TO_ACE.md fully
□ Read and document INTEGRATION_GUIDE.md fully
□ Analyze claude-code-loop example implementation
□ Document all public classes and methods in ace/core/
□ Document all configuration options with defaults
□ Understand LiteLLM client initialization
□ Document skill extraction algorithm
□ Document reflection prompt templates
□ Verify async learning thread safety patterns
□ Identify all extension/customization points
□ Document error handling patterns
□ Check for environment variable requirements
</verification_checklist>

<research_quality_assurance>
<completeness_check>
- [ ] All official documentation files read
- [ ] All example implementations analyzed
- [ ] Source code for core components reviewed
- [ ] Configuration options enumerated with descriptions
- [ ] API key and environment requirements documented
</completeness_check>

<source_verification>
- [ ] Primary claims backed by source code
- [ ] Configuration options verified against actual implementation
- [ ] Example patterns confirmed working
- [ ] Version and compatibility requirements documented
</source_verification>

<blind_spots_review>
- [ ] Are there undocumented features in source code?
- [ ] Are there breaking changes in recent commits?
- [ ] Are there known issues or limitations documented in issues?
- [ ] Are there alternative usage patterns not in docs?
</blind_spots_review>
</research_quality_assurance>

<output_structure>
Save to: `.prompts/006-ace-docs-research/ace-docs-research.md`

Write findings incrementally as you discover them:

1. Create the file with initial structure
2. Append each finding as discovered
3. Update metadata at the end

```xml
<research>
  <summary>
    {2-3 paragraph executive summary of ACE framework capabilities}
  </summary>

  <findings>
    <finding category="architecture">
      <title>{Component name}</title>
      <detail>{How it works, responsibilities}</detail>
      <source>{File/doc where found}</source>
      <relevance>{Why RALPH needs this}</relevance>
    </finding>
    <!-- Continue for each major component/concept -->
  </findings>

  <configuration_reference>
    <option name="{config_name}">
      <type>{data type}</type>
      <default>{default value}</default>
      <description>{what it does}</description>
      <example>{usage example}</example>
    </option>
    <!-- All configuration options -->
  </configuration_reference>

  <code_examples>
    <example name="{pattern_name}">
      {Code snippet with context}
      Source: {file path}
    </example>
  </code_examples>

  <recommendations>
    <recommendation priority="high">
      <action>{What RALPH should do}</action>
      <rationale>{Why based on ACE docs}</rationale>
    </recommendation>
  </recommendations>

  <metadata>
    <confidence level="{high|medium|low}">
      {Why this confidence level}
    </confidence>
    <dependencies>
      - Python packages required
      - Environment variables needed
      - Model access requirements
    </dependencies>
    <open_questions>
      {What couldn't be determined}
    </open_questions>
    <assumptions>
      {What was assumed}
    </assumptions>

    <quality_report>
      <sources_consulted>
        {List all files and URLs read}
      </sources_consulted>
      <claims_verified>
        {Key findings verified with source code}
      </claims_verified>
      <claims_assumed>
        {Findings based on inference}
      </claims_assumed>
    </quality_report>
  </metadata>
</research>
```
</output_structure>

<summary_requirements>
Create `.prompts/006-ace-docs-research/SUMMARY.md`

Must include:
- **One-liner**: Substantive description (not "Research completed")
- **Key Findings**: 5-7 actionable takeaways
- **Critical Configuration**: Most important options for RALPH
- **Decisions Needed**: What requires human input
- **Blockers**: External impediments
- **Next Step**: "Create RALPH integration research"
</summary_requirements>

<success_criteria>
- All ACE documentation files fully analyzed
- All configuration options enumerated with descriptions
- Core component responsibilities clearly documented
- Integration patterns extracted with code examples
- API key / environment requirements documented
- Ready for RALPH integration research to consume
- SUMMARY.md created with substantive findings
</success_criteria>
