# CEN 4010 - Principles of Software Engineering
## Guide to Canonical Architectures for Agentic AI Pipelines

> **Source:** `CEN4010 - Guide to Canonical Architectures.pdf` (uploaded file)
> Referenced by: [`CEN4010 - Assignment 1`](./CEN4010%20-%20Assignment%201.md)
>
> *This report is maintained by Agentic AI.*

This guide presents the eight canonical architectures for Agentic AI Pipelines. Each entry includes its solution architecture, explanation, architecture elements, and execution sequence.

1. [Document Intelligence Agentic AI Pipeline](#1-document-intelligence-agentic-ai-pipeline)
2. [Knowledge Intelligence Agentic AI Pipeline](#2-knowledge-intelligence-agentic-ai-pipeline)
3. [Data Intelligence Agentic AI Pipeline](#3-data-intelligence-agentic-ai-pipeline)
4. [Decision Intelligence Agentic AI Pipeline](#4-decision-intelligence-agentic-ai-pipeline)
5. [Conversational Intelligence Agentic AI Pipeline](#5-conversational-intelligence-agentic-ai-pipeline)
6. [Case and Workflow Intelligence Agentic AI Pipeline](#6-case-and-workflow-intelligence-agentic-ai-pipeline)
7. [Operational Intelligence Agentic AI Pipeline](#7-operational-intelligence-agentic-ai-pipeline)
8. [Generative Engineering Intelligence Agentic AI Pipeline](#8-generative-engineering-intelligence-agentic-ai-pipeline)

---

## (1) Document Intelligence Agentic AI Pipeline

This architecture works by registering source documents, extracting candidate information, associating facts, validating the result, and composing a reviewable work product. It connects source documents and operating context to validated, source-aware information and a report, brief, extract, or knowledge matrix. GenAI models are applied to document content and operating context to extract, associate, and compose candidate information.

**Solution architecture flow:** Source Documents → API / CLI Ingestion → Document Store → GenAI Extraction Service → Knowledge / Fact Store ↔ Human Review Workbench ↔ GenAI Report Service → Reviewable Report / Work Product → Authorized Reviewer / Decision Maker

**Architecture elements**

- **API / CLI Ingestion:** Receives source documents and registers them.
- **Document Store:** Retains the source documents and their metadata.
- **GenAI Extraction Service:** Produces source-linked candidate information.
- **Knowledge / Fact Store:** Supports retrieval and association of candidate information.
- **Human Review Workbench:** Validates information and sends corrections.
- **GenAI Report Service:** Produces a report or other work product from reviewed information.
- **Authorized Reviewer / Decision Maker:** Keeps final authority outside the pipeline.

**Step-by-step explanation**

1. A user, upstream system, or command submits one or more source documents through the API or CLI. The ingestion service assigns an identifier and records source, submission time, file type, and other available metadata in the document store.
2. The GenAI Extraction Service receives the document content and the task context. It identifies candidate facts, classifications, and relationships, then records a source reference for each candidate item so a reviewer can trace it back to the material that supports it.
3. The Knowledge / Fact Store associates the candidate information with related documents, records, or topics. Candidate information remains distinct from validated information so later retrieval does not represent an unreviewed extraction as an approved fact.
4. A reviewer opens the Human Review Workbench to compare candidate information with its source material. The reviewer can validate it, correct it, reject it, or mark a question that requires more information before the workflow continues.
5. The GenAI Report Service composes a report, brief, extract, or knowledge matrix from the reviewed information and relevant sources. The authorized reviewer accepts the work product or sends instructions for another revision cycle.

---

## (2) Knowledge Intelligence Agentic AI Pipeline

This architecture works by collecting distributed sources, structuring and cataloging candidate knowledge, governing approved records, and retrieving controlled context. It connects documents, databases, messages, and other sources to a reusable knowledge store and retrieval interface. GenAI models are applied to source material and retrieval context to structure, label, and retrieve candidate knowledge.

**Solution architecture flow:** Documents, Databases, Messages → Source Connectors → GenAI Normalize + Catalog Service → Knowledge Store + Index ↔ Knowledge Steward Workbench / Retrieval API → AI-enabled Workflows

**Architecture elements**

- **Source Connectors:** Collect documents, databases, messages, and other sources.
- **GenAI Normalize + Catalog Service:** Structures and labels candidate knowledge.
- **Knowledge Store + Index:** Preserves approved knowledge and provenance.
- **Knowledge Steward Workbench:** Reviews corrections and governs stored knowledge.
- **Retrieval API:** Supplies controlled context to AI-enabled workflows.

**Step-by-step explanation**

1. Source Connectors collect approved documents, records, messages, database entries, and other source material. Each collected item retains its source identity so later users can determine where the knowledge originated.
2. The GenAI Normalize + Catalog Service reads the source material and creates structured candidate knowledge. It can label topics, summarize content, relate records, and prepare metadata that makes later retrieval possible.
3. A knowledge steward reviews the candidate record in the workbench before it becomes reusable organizational knowledge. The steward corrects, approves, rejects, or restricts the record according to knowledge-governance rules.
4. The Knowledge Store + Index retains approved content together with provenance, version context, and access rules. The index makes approved content findable without exposing records that are not authorized for the request.
5. A workflow or user-facing service submits a retrieval request through the API. The API returns controlled, relevant context that can support an answer, a decision, or a subsequent AI task.

---

## (3) Data Intelligence Agentic AI Pipeline

This architecture works by ingesting recurring data and signals, preparing them for analysis, applying models, and monitoring the result. It connects data, sensors, and events to monitored forecasts, classifications, anomaly signals, or recommendations. GenAI models are applied to prepared data, signals, and analytical context to interpret results and formulate outputs.

**Solution architecture flow:** Data + Sensors → Batch / Stream Ingestion → Data Store → AI Model Service ↔ Validation + Monitoring Workbench → Forecast / Recommendation Service ↔ Validation + Monitoring Workbench → Decision or Workflow Input

**Architecture elements**

- **Batch / Stream Ingestion:** Receives recurring data and sensor signals.
- **Data Store:** Retains prepared data for analysis.
- **AI Model Service:** Produces forecasts, classifications, or anomaly signals.
- **Forecast / Recommendation Service:** Formats model output for a consumer.
- **Validation + Monitoring Workbench:** Reviews quality, drift, and feedback.

**Step-by-step explanation**

1. Batch / Stream Ingestion receives scheduled files, event streams, sensor signals, or other recurring observations. It records when the data arrived and which source produced it so the analysis has clear time and source context.
2. The Data Store retains the prepared data set that the analysis will use. This separates the analytical input from the incoming feed and provides a stable record for review or repeated analysis.
3. The AI Model Service analyzes the prepared data and produces a forecast, classification, anomaly signal, or other analytical result. GenAI models can interpret the analytical context or explain the result, while the service preserves the underlying signal and model output.
4. The Forecast / Recommendation Service translates the model output into a result that a person or downstream workflow can use. It presents the relevant measure, condition, or recommended next action without turning the output into an unreviewed decision.
5. The Validation + Monitoring Workbench checks input quality, output quality, drift, and user feedback over time. It identifies when the result remains usable, requires investigation, or must be restricted until the data or model is reviewed.

---

## (4) Decision Intelligence Agentic AI Pipeline

This architecture works by assembling evidence and rules, framing options, applying policy, and routing the result to the appropriate authority. It connects data, models, knowledge, and rules to a recommendation, permitted action, or escalation. GenAI models are applied to assembled evidence, rules, and candidate options to frame a decision for review.

**Solution architecture flow:** Data, Models, Knowledge, Rules → Context + Rules Integration → GenAI Option Framing Service ↔ Decision Review Workbench → Policy Engine ↔ Decision Review Workbench → Recommendation / Action / Escalation → Authorized Decision Maker

**Architecture elements**

- **Context + Rules Integration:** Assembles evidence, models, knowledge, and rules.
- **GenAI Option Framing Service:** Produces candidate options for review.
- **Policy Engine:** Applies the permitted decision rules.
- **Decision Review Workbench:** Supports review, override, and escalation.
- **Authorized Decision Maker:** Accepts the recommendation, action, or escalation.

**Step-by-step explanation**

1. Context + Rules Integration assembles the evidence, analytical outputs, organizational knowledge, and applicable rules for one decision situation. It establishes the information that the pipeline may use before it frames options.
2. The GenAI Option Framing Service applies models to the assembled context and prepares candidate options with supporting rationale. The service proposes alternatives for review; it does not hold authority to make the final decision.
3. The Policy Engine evaluates the candidate options against permitted rules, thresholds, and restrictions. It identifies which actions are allowed, which need further approval, and which require escalation.
4. The Decision Review Workbench presents the recommendation, the policy result, and the supporting evidence to the reviewer. The reviewer can inspect the basis, override the recommendation when authorized, or route the matter to a higher authority.
5. The Authorized Decision Maker accepts an action, selects an alternative, or escalates the decision. The resulting decision and its basis become the accountable outcome of the pipeline.

---

## (5) Conversational Intelligence Agentic AI Pipeline

This architecture works by receiving an interaction, interpreting user intent, retrieving relevant context, guiding dialogue, and transferring work when needed. It connects a user or channel to a response, transaction, completed interaction, or human handoff. GenAI models are applied to user messages and retrieved context to interpret intent and produce dialogue.

**Solution architecture flow:** User / Channel → Conversation Gateway → GenAI Intent + Dialogue Service → Conversation Orchestrator ↔ Context Retrieval Service ↔ Knowledge + Context Store → Response / Transaction → Human Handoff (correction loop back to Conversation Orchestrator)

**Architecture elements**

- **User / Channel:** Receives messages or other interaction input.
- **Conversation Gateway:** Manages the incoming interaction session.
- **GenAI Intent + Dialogue Service:** Interprets intent and produces the next dialogue turn.
- **Context Retrieval Service:** Retrieves relevant information for the interaction.
- **Knowledge + Context Store:** Retains approved knowledge and conversation context.
- **Conversation Orchestrator:** Coordinates retrieval, dialogue, and permitted actions.
- **Human Handoff:** Transfers an interaction that needs human work or authority.

**Step-by-step explanation**

1. A user sends a message through a supported channel, such as chat, web, voice, or a service interface. The Conversation Gateway starts or resumes the interaction session and retains the message with its session context.
2. The GenAI Intent + Dialogue Service interprets the message, identifies the current user need, and prepares a candidate response or next dialogue turn. It uses the interaction content to guide the conversation rather than treating a single message in isolation.
3. The Context Retrieval Service requests relevant approved knowledge and conversation history. The Knowledge + Context Store returns only the material that the interaction is permitted to use.
4. The Conversation Orchestrator combines the candidate dialogue with retrieved context and determines which permitted action, if any, the workflow can take. It coordinates the response, retrieval, and action without allowing the model to bypass established controls.
5. The pipeline returns a response, completes a permitted transaction, or identifies that the interaction requires human work or authority. In that case, Human Handoff transfers the context and open work to the appropriate person.

---

## (6) Case and Workflow Intelligence Agentic AI Pipeline

This architecture works by registering a case trigger, establishing its state, coordinating tasks and handoffs, monitoring deadlines, and recording the outcome. It connects a request, case, or event to coordinated multi-step work, an outcome record, or an escalation. GenAI models are applied to case information and workflow state to interpret requests and prepare candidate next steps.

**Solution architecture flow:** Case Trigger → Case Intake Service → Case Record + State Store ↔ Deadline + SLA Monitor → Workflow Orchestrator → Task + Queue Service ↔ Human Workbench ↔ Outcome + Audit Record → Completed Case / Escalation

**Architecture elements**

- **Case Intake Service:** Registers a request, case, or event.
- **Case Record + State Store:** Retains ownership, status, deadlines, and case history.
- **Workflow Orchestrator:** Directs the next permitted step and handoff.
- **Task + Queue Service:** Assigns and tracks work across people or systems.
- **Deadline + SLA Monitor:** Detects overdue work and timing risks.
- **Human Workbench:** Supports work, review, approvals, and exceptions.
- **Outcome + Audit Record:** Preserves the completed result and decision trail.

**Step-by-step explanation**

1. The Case Intake Service receives a request, case trigger, or event and creates the initial case record. The record identifies the work item and establishes the state from which the workflow will begin.
2. The Case Record + State Store retains ownership, status, deadlines, history, and the information needed to coordinate the case. It gives each participant a shared view of the current state rather than relying on disconnected messages or personal notes.
3. The Workflow Orchestrator applies GenAI models to the case information and current state to interpret the request and prepare candidate next steps. The orchestrator limits those proposals to steps that the workflow and policy permit.
4. The Task + Queue Service assigns work to people or systems and tracks each handoff. The Deadline + SLA Monitor observes the timing rules and alerts the workflow when work is overdue or at risk.
5. People use the Human Workbench to complete tasks, review results, approve exceptions, or escalate unresolved work. Their actions update the case state and determine whether the workflow advances, pauses, or changes route.
6. When the work reaches an outcome, the Outcome + Audit Record preserves the result, key decisions, and the history of significant actions. This record supports later review, accountability, and any follow-up work.

---

## (7) Operational Intelligence Agentic AI Pipeline

This architecture works by observing telemetry and operational state, diagnosing conditions, selecting a permitted response, executing it, and verifying the result. It connects telemetry, operational events, and system state to a controlled response, recovery, or escalation. GenAI models are applied to telemetry, events, and operating state to diagnose conditions and propose a response.

**Solution architecture flow:** Telemetry + Events → Operational State Store ↔ GenAI Diagnosis Service (observation loop) → Response + Policy Engine ↔ Operator Workbench (override loop) → Automation Executor ↔ Verification + Monitoring → Recovery / Escalation

**Architecture elements**

- **Telemetry + Events:** Collects operational signals and observed conditions.
- **Operational State Store:** Retains current and historical system state.
- **GenAI Diagnosis Service:** Interprets conditions and identifies candidate causes.
- **Response + Policy Engine:** Selects a permitted response under operating rules.
- **Automation Executor:** Carries out an approved automated response.
- **Verification + Monitoring:** Checks the result and records new observations.
- **Operator Workbench:** Supports overrides, recovery work, and escalation.

**Step-by-step explanation**

1. Telemetry + Events collects signals, alerts, logs, and other observations from the operating environment. Each observation records the condition, time, and source that triggered the pipeline.
2. The Operational State Store combines current observations with relevant historical state. This gives the diagnosis process the context needed to distinguish a new condition from a recurring or already-resolved one.
3. The GenAI Diagnosis Service interprets the signals and operational context to identify candidate causes and potential responses. Its output is an explanation or proposal that the response controls must still evaluate.
4. The Response + Policy Engine evaluates the proposed response against operating rules, safety boundaries, and approval requirements. It selects a permitted response or routes the condition for human review when the response is outside those boundaries.
5. The Automation Executor carries out an approved response. Verification + Monitoring observes the subsequent state to determine whether the response changed the condition as expected or whether the pipeline must continue.
6. An operator uses the Operator Workbench when automation cannot safely resolve the condition or a person must take authority. The operator can override, perform recovery work, or escalate the incident with the diagnostic context and action history available.

---

## (8) Generative Engineering Intelligence Agentic AI Pipeline

This architecture works by planning work, generating candidate artifacts, testing and reviewing them, and recording release or revision decisions. It connects requirements, constraints, and feedback to a validated engineered artifact. GenAI models are applied to requirements, constraints, and feedback to plan work and produce candidate artifacts.

**Solution architecture flow:** Requirements + Constraints → Planning + Task Service (feedback loop) → GenAI Artifact Service ↔ Artifact Workspace / Repository ↔ Test + Validation Service (defect/revision loop) → Human Engineering Review ↔ Release / Revision Record → Validated Artifact / Release

**Architecture elements**

- **Requirements + Constraints:** Defines the target, limits, and acceptance basis.
- **Planning + Task Service:** Breaks the target into reviewable work.
- **GenAI Artifact Service:** Produces candidate code, designs, configurations, or content.
- **Artifact Workspace / Repository:** Retains generated artifacts and their history.
- **Test + Validation Service:** Evaluates an artifact against its requirements and checks.
- **Human Engineering Review:** Reviews quality, risks, and release readiness.
- **Release / Revision Record:** Preserves the approved release or next revision decision.

**Step-by-step explanation**

1. Requirements + Constraints define the engineering target, its boundaries, and the acceptance basis that a completed artifact must satisfy. They give the pipeline a traceable reference for deciding whether a candidate artifact is suitable.
2. The Planning + Task Service divides the target into reviewable tasks and identifies relevant dependencies. This work plan gives generation, validation, and human review a shared sequence of work.
3. The GenAI Artifact Service applies models to the approved requirements, constraints, and task context. It produces candidate code, designs, configurations, or content that remain subject to validation and engineering review.
4. The Artifact Workspace / Repository records each candidate artifact, its source context, and its revision history. It provides a controlled place to compare versions and trace changes back to the work that produced them.
5. The Test + Validation Service evaluates the candidate against requirements, constraints, and defined quality checks. It records evidence that the artifact passes, fails, or needs further investigation before release.
6. A person uses Human Engineering Review to assess quality, risk, and release readiness in light of the validation evidence. The Release / Revision Record preserves the approval or requested revision and starts the next cycle when work remains.

---
*Converted to Markdown from the original PDF (`CEN4010 - Guide to Canonical Architectures.pdf`) uploaded by Caleb.*
