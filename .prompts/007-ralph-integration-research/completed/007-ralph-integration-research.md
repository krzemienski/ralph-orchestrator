# RALPH Orchestrator Integration Points Research

<session_initialization>
Before beginning research, verify today's date:
!`date +%Y-%m-%d`
</session_initialization>

<research_objective>
Research the RALPH orchestrator codebase to identify all integration points where ACE learning capabilities should be connected.

Purpose: Map RALPH's architecture to ACE integration requirements
Scope: RALPH source code, existing learning module, adapter patterns
Output: ralph-integration-research.md with integration blueprint
</research_objective>

<context>
ACE Documentation Research: @.prompts/006-ace-docs-research/ace-docs-research.md

Use the ACE research findings to identify where RALPH needs modification.
</context>

<research_scope>
<include>
**Core Orchestration Loop:**
- `orchestrator.py` - Main execution loop
- `arun()` method structure
- `_aexecute_iteration()` implementation
- Iteration lifecycle hooks

**Existing Learning Module:**
- `src/ralph_orchestrator/learning/` directory
- Current `ace_adapter.py` implementation
- What works, what's broken
- Gap analysis vs ACE best practices

**Adapter Architecture:**
- `adapters/base.py` - Base adapter interface
- `adapters/claude.py` - Claude adapter
- `adapters/acp.py` - ACP adapter
- `_enhance_prompt_with_instructions()` method
- How prompts are constructed

**Context Management:**
- `context.py` - Context manager
- Dynamic context injection
- `.agent/scratchpad.md` pattern
- How context flows to adapters

**Metrics & Logging:**
- `metrics.py` - Iteration metrics
- `verbose_logger.py` - Tool call tracking
- What data is available for reflection

**Configuration:**
- `main.py` - CLI configuration
- `--learning` flag handling
- Environment variable propagation
</include>

<exclude>
- ACE internal implementation (covered in prior research)
- UI/Web components
- Test infrastructure details
</exclude>

<sources>
**Primary - RALPH Source Code:**
- src/ralph_orchestrator/orchestrator.py
- src/ralph_orchestrator/learning/ace_adapter.py
- src/ralph_orchestrator/adapters/base.py
- src/ralph_orchestrator/adapters/claude.py
- src/ralph_orchestrator/adapters/acp.py
- src/ralph_orchestrator/context.py
- src/ralph_orchestrator/metrics.py
- src/ralph_orchestrator/main.py
- src/ralph_orchestrator/__init__.py

**Documentation:**
- CLAUDE.md files in src directories
- docs/guide/ documentation
- Any existing integration guides
</sources>
</research_scope>

<verification_checklist>
□ Map complete execution flow from `ralph run` to completion
□ Identify exact location for skillbook injection
□ Identify exact location for learning trigger
□ Document data available at each lifecycle point
□ Analyze current ace_adapter.py bugs and gaps
□ Verify environment variable propagation path
□ Check async/threading compatibility
□ Document all adapter hook points
□ Identify metrics useful for reflection
□ Map configuration flow from CLI to components
</verification_checklist>

<research_quality_assurance>
<completeness_check>
- [ ] All relevant source files read
- [ ] Execution flow fully traced
- [ ] All integration points identified
- [ ] Data flow documented
- [ ] Current bugs identified
</completeness_check>

<gap_analysis>
Compare RALPH's current state against ACE requirements:
- [ ] Does RALPH provide execution output ACE needs?
- [ ] Can RALPH inject skillbook context properly?
- [ ] Is async learning thread-safe in RALPH?
- [ ] Are environment variables propagated correctly?
</gap_analysis>
</research_quality_assurance>

<output_structure>
Save to: `.prompts/007-ralph-integration-research/ralph-integration-research.md`

```xml
<research>
  <summary>
    {Executive summary of RALPH architecture and ACE integration fit}
  </summary>

  <execution_flow>
    <step order="1">
      <location>{file:line}</location>
      <description>{What happens}</description>
      <data_available>{What data exists here}</data_available>
      <integration_opportunity>{How ACE could connect}</integration_opportunity>
    </step>
    <!-- Complete execution flow -->
  </execution_flow>

  <integration_points>
    <point id="skillbook-injection">
      <file>{file path}</file>
      <method>{method name}</method>
      <description>{How to inject skillbook}</description>
      <code_change>{Required modification}</code_change>
    </point>

    <point id="learning-trigger">
      <file>{file path}</file>
      <method>{method name}</method>
      <description>{When to trigger learning}</description>
      <data_for_reflection>{What to pass to ACE}</data_for_reflection>
    </point>
    <!-- All integration points -->
  </integration_points>

  <current_bugs>
    <bug id="api-key-propagation">
      <file>{file}</file>
      <description>{What's broken}</description>
      <root_cause>{Why it's broken}</root_cause>
      <fix>{How to fix}</fix>
    </bug>
    <!-- All identified bugs -->
  </current_bugs>

  <data_mapping>
    <ralph_data>{What RALPH provides}</ralph_data>
    <ace_requirement>{What ACE needs}</ace_requirement>
    <transformation>{How to map between them}</transformation>
  </data_mapping>

  <recommendations>
    <recommendation priority="critical">
      <action>{What to change}</action>
      <rationale>{Why, based on research}</rationale>
      <files_affected>{List of files}</files_affected>
    </recommendation>
  </recommendations>

  <metadata>
    <confidence level="{high|medium|low}">
      {Confidence in integration approach}
    </confidence>
    <dependencies>
      - ACE research findings
      - API key availability
      - Thread safety requirements
    </dependencies>
    <open_questions>
      {Uncertainties about integration}
    </open_questions>
    <assumptions>
      {Assumptions about RALPH behavior}
    </assumptions>

    <quality_report>
      <sources_consulted>
        {All RALPH files read}
      </sources_consulted>
      <verified_vs_assumed>
        {What was verified by reading code vs assumed}
      </verified_vs_assumed>
    </quality_report>
  </metadata>
</research>
```
</output_structure>

<summary_requirements>
Create `.prompts/007-ralph-integration-research/SUMMARY.md`

Must include:
- **One-liner**: Substantive finding about integration feasibility
- **Key Integration Points**: File:method pairs for modification
- **Current Bugs**: Critical issues to fix
- **Data Flow**: How learning data moves through system
- **Decisions Needed**: Architecture choices for user
- **Blockers**: Technical impediments
- **Next Step**: "Create ACE-RALPH integration plan"
</summary_requirements>

<success_criteria>
- Complete execution flow mapped with file:line references
- All integration points identified with code change descriptions
- Current bugs in ace_adapter.py documented with fixes
- Data mapping between RALPH metrics and ACE requirements
- Clear recommendations prioritized by criticality
- Ready for planning phase to consume
- SUMMARY.md created with integration blueprint
</success_criteria>
