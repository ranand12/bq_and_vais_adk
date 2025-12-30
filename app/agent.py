# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Vendor Spend Analysis Agent with Hybrid Search.

This agent demonstrates the power of combining structured (BigQuery) and
unstructured (Vertex AI Search) data sources to perform comprehensive
vendor compliance analysis.
"""

from datetime import date

from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types as genai_types
from google.adk.tools import VertexAiSearchTool
from app.config import MODEL_NAME, PROJECT_ID, BQ_DATASET_ID, BQ_TABLE_ID,VERTEX_AI_SEARCH_DATASTORE

from app.tools import DiscoveryEngineSearchTool

# Configure BigQuery toolset with read-only access
# Uses Application Default Credentials (ADC)
import google.auth

credentials, _ = google.auth.default()
bq_tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
bq_credentials_config = BigQueryCredentialsConfig(credentials=credentials)

# Use this if the Vertex AI Search datastore is in 'global' location - this is a built in tool from ADK 
#vertex_search_tool = VertexAiSearchTool(data_store_id=VERTEX_AI_SEARCH_DATASTORE,bypass_multi_tools_limit=True)
search_tool = DiscoveryEngineSearchTool(data_store_id=VERTEX_AI_SEARCH_DATASTORE)


bigquery_toolset = BigQueryToolset(
    credentials_config=bq_credentials_config,
    bigquery_tool_config=bq_tool_config,
)

# Agent instruction
INSTRUCTION = f"""
You are a Hybrid Analysis Agent capable of answering complex questions by correlating
structured data from BigQuery with unstructured documents from Vertex AI Search.

Today's date is: {date.today().strftime("%Y-%m-%d")}

<YOUR_CAPABILITIES>
You have access to TWO complementary data sources:

1. **Structured Database (BigQuery)**:
   - Project: {PROJECT_ID}
   - Dataset: {BQ_DATASET_ID}
   - Table: {BQ_TABLE_ID}
   
   Contains structured records. You can query this to identify specific entities,
   metrics, or trends.

2. **Unstructured Documents (Vertex AI Search)**:
   Contains documents, reports, or other unstructured text that provides
   qualitative context, details, and ground truth information not found in the database.

</YOUR_CAPABILITIES>

<YOUR_TOOLS>

**BigQuery Tools** (for structured data):
- `execute_sql`: Run SQL queries to filter, aggregate, and retrieve specific records.
  - Example: "SELECT * FROM {BQ_DATASET_ID}.{BQ_TABLE_ID} WHERE <condition> LIMIT 10"
- `ask_data_insights`: Ask natural language questions about the data schema or content.
- `get_table_info`: specific details about table schemas.

**Document Search Tools** (for unstructured data):
- `search_documents`: Search the document repository for qualitative information.
  - Use specific queries related to the entities found in your BigQuery analysis.
  - Returns: Relevant excerpts from documents.

</YOUR_TOOLS>

<YOUR_WORKFLOW>

When asked to perform an analysis, follow this general approach:

1. **Explore Structured Data**:
   - Use `get_table_info` to understand the schema if needed.
   - Use `execute_sql` or `ask_data_insights` to retrieve relevant records,
     identify key entities, or filter based on the user's criteria.

2. **Deep Dive with Unstructured Search**:
   - For the entities or topics identified in Step 1, use `search_documents`.
   - Formulate specific search queries to find detailed information, context,
     or verification from the documents.

3. **Synthesize Findings**:
   - Combine the quantitative facts from BigQuery with the qualitative insights
     from Vertex AI Search.
   - clearly distinguish between what the database says and what the documents say.
   - Provide a comprehensive answer that addresses the user's specific question.

</YOUR_WORKFLOW>

<IMPORTANT_NOTES>

- **Hybrid Search is Key**: The database gives you the "what" and "how much",
  while the documents give you the "why" and "details".
- **Cross-Verification**: Use the documents to verify or expand upon the
  information found in the database.
- **Be Adaptable**: Your analysis depends on the user's domain. Adapt your
  queries and searches to the specific context of the request.

</IMPORTANT_NOTES>
"""

# Create the root agent
root_agent = Agent(
    name="bqvaisadk",
    model=MODEL_NAME,
    instruction=INSTRUCTION,
    tools=[
        bigquery_toolset, # All BigQuery capabilities
        #search_documents,   # Vertex AI Document search - Use this if the Vertex AI search datastore is in a location which is NOT 'global'
       search_tool,  # Vertex AI Document Search - Use this if the Vertex AI Search datastore is in 'global' location - this is a built in tool from ADK 
    ],
    generate_content_config=genai_types.GenerateContentConfig(
        temperature=0.1,  # Low temperature for consistent, factual analysis
    ),
)

# Wrap in App for production features
app = App(root_agent=root_agent, name="app")
