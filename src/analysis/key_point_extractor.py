"""
Key point extraction module using Ollama LLM.
"""

from loguru import logger
import json
from pathlib import Path
import re
import tempfile

try:
    import ollama
    from langchain_community.llms import Ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    logger.warning("Ollama not available. Will use fallback extraction mechanism.")
    OLLAMA_AVAILABLE = False

from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain

from utils.error_handler import error_handler, AnalysisError
from utils.config import Config


class KeyPointExtractor:
    """
    Class to extract key points from tender documents using Ollama LLM.
    """
    
    def __init__(self, vector_store):
        """
        Initialize the key point extractor.
        
        Args:
            vector_store: FAISS vector store containing document chunks.
        """
        self.vector_store = vector_store
        self.key_points = Config.KEY_POINTS
        
        if OLLAMA_AVAILABLE:
            self._init_llm()
        else:
            logger.info("Using fallback extraction mechanism instead of Ollama")
        
        logger.debug("KeyPointExtractor initialized")
    
    @error_handler
    def _init_llm(self):
        """Initialize the Ollama LLM."""
        try:
            logger.debug(f"Initializing Ollama LLM with model {Config.OLLAMA_MODEL}")
            
            # Initialize Ollama LLM
            self.llm = Ollama(
                model=Config.OLLAMA_MODEL,
                base_url=Config.OLLAMA_API_BASE,
                temperature=0.1,  # Lower temperature for more focused responses
            )
            
            logger.debug("Ollama LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {str(e)}")
            logger.info("Will use fallback extraction mechanism")
            global OLLAMA_AVAILABLE
            OLLAMA_AVAILABLE = False
    
    @error_handler
    def extract_key_points(self):
        """
        Extract key points from the vector store.
        
        Returns:
            dict: Dictionary containing extracted key points.
        """
        logger.info("Extracting key points from tender document")
        
        # Dictionary to store extracted key points
        extracted_points = {}
        
        # Process each key point
        for key_point in self.key_points:
            logger.info(f"Extracting information about '{key_point}'")
            extracted_info = self._extract_single_point(key_point)
            extracted_points[key_point] = extracted_info
        
        return extracted_points
    
    @error_handler
    def _extract_single_point(self, key_point):
        """
        Extract a single key point from the vector store.
        
        Args:
            key_point (str): The key point to extract.
            
        Returns:
            str: Extracted information about the key point.
        """
        # Create search query based on key point
        search_query = self._create_search_query(key_point)
        
        # Retrieve relevant chunks
        relevant_chunks = self._retrieve_relevant_chunks(search_query)
        
        # Extract information using LLM or fallback
        if OLLAMA_AVAILABLE:
            extracted_info = self._process_with_llm(key_point, relevant_chunks)
        else:
            extracted_info = self._process_with_fallback(key_point, relevant_chunks)
        
        return extracted_info
    
    @error_handler
    def _process_with_fallback(self, key_point, context):
        """
        Process the context with a fallback rule-based approach when LLM is not available.
        
        Args:
            key_point (str): The key point to extract.
            context (str): The context from relevant chunks.
            
        Returns:
            str: Extracted information about the key point.
        """
        logger.debug(f"Using fallback extraction for {key_point}")
        
        # Simple rule-based extraction based on the key point
        result = []
        
        if key_point == "Deadline":
            # Look for dates and deadline-related information
            date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b'
            deadline_pattern = r'\b(?:deadline|due date|submission|due by|complete by|deliver by|finish by)[^\n.]*(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})[^\n.]*'
            
            # Extract dates
            dates = re.findall(date_pattern, context, re.IGNORECASE)
            deadlines = re.findall(deadline_pattern, context, re.IGNORECASE)
            
            if dates or deadlines:
                result.append("Deadline information:")
                for date in dates:
                    result.append(f"- Date found: {date}")
                for deadline in deadlines:
                    result.append(f"- {deadline.strip()}")
            else:
                result.append("No specific deadline information found in the document.")
        
        elif key_point == "Project Requirement":
            # Look for requirement information
            # Find sections that might contain requirements
            requirement_sections = re.findall(r'(?:requirements|specifications|scope)[^\n]*\n+(?:[\s\S]*?)(?=\n\s*\n|\Z)', context, re.IGNORECASE)
            
            # Extract bullet points
            bullet_points = re.findall(r'[-•*]\s+([^\n]+)', context)
            
            if requirement_sections or bullet_points:
                result.append("Project Requirements:")
                
                # Add a few representative sections
                for i, section in enumerate(requirement_sections[:3]):  # Limit to 3 sections
                    cleaned_section = re.sub(r'\s+', ' ', section).strip()
                    result.append(f"- Requirement section: {cleaned_section[:150]}...")
                
                # Add bullet points
                for point in bullet_points[:10]:  # Limit to 10 bullet points
                    result.append(f"- {point.strip()}")
            else:
                result.append("No specific project requirements found in the document.")
        
        elif key_point == "Cost":
            # Look for cost and budget information
            cost_pattern = r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?'
            payment_pattern = r'(?:payment|budget|cost|price|fee|financial)[^\n.]*'
            
            costs = re.findall(cost_pattern, context)
            payment_info = re.findall(payment_pattern, context, re.IGNORECASE)
            
            if costs or payment_info:
                result.append("Cost and Payment Information:")
                if costs:
                    result.append("Financial figures mentioned:")
                    for cost in costs[:5]:  # Limit to 5 figures
                        result.append(f"- {cost}")
                
                if payment_info:
                    result.append("Payment terms mentioned:")
                    for info in payment_info[:5]:  # Limit to 5 terms
                        cleaned_info = re.sub(r'\s+', ' ', info).strip()
                        if len(cleaned_info) > 10:  # Only if meaningful
                            result.append(f"- {cleaned_info}")
            else:
                result.append("No specific cost information found in the document.")
        
        elif key_point == "Quality Checking":
            # Look for quality control information
            quality_pattern = r'(?:quality|testing|assurance|certification|compliance|standard)[^\n.]*'
            
            quality_info = re.findall(quality_pattern, context, re.IGNORECASE)
            hardware_info = re.findall(r'(?:hardware|server|equipment|device)[^\n.]*', context, re.IGNORECASE)
            software_info = re.findall(r'(?:software|application|system|code|program)[^\n.]*', context, re.IGNORECASE)
            
            if quality_info or hardware_info or software_info:
                result.append("Quality Checking Information:")
                
                if quality_info:
                    result.append("Quality standards mentioned:")
                    for info in quality_info[:5]:
                        cleaned_info = re.sub(r'\s+', ' ', info).strip()
                        if len(cleaned_info) > 10:
                            result.append(f"- {cleaned_info}")
                
                if hardware_info:
                    result.append("Hardware specifications:")
                    for info in hardware_info[:3]:
                        cleaned_info = re.sub(r'\s+', ' ', info).strip()
                        if len(cleaned_info) > 10:
                            result.append(f"- {cleaned_info}")
                
                if software_info:
                    result.append("Software requirements:")
                    for info in software_info[:3]:
                        cleaned_info = re.sub(r'\s+', ' ', info).strip()
                        if len(cleaned_info) > 10:
                            result.append(f"- {cleaned_info}")
            else:
                result.append("No specific quality checking information found in the document.")
        
        # Combine results
        return "\n".join(result)
    
    @error_handler
    def _create_search_query(self, key_point):
        """
        Create a search query for the key point.
        
        Args:
            key_point (str): The key point to search for.
            
        Returns:
            str: Search query.
        """
        query_templates = {
            "Deadline": "deadline submission due date timeline schedule",
            "Project Requirement": "project requirements specifications scope of work technical requirements",
            "Cost": "cost budget price financial milestone payment terms payment schedule financial terms",
            "Quality Checking": "quality control quality assurance testing hardware software requirements quality standards"
        }
        
        base_query = query_templates.get(key_point, key_point)
        return f"Find information about {key_point} in tender document: {base_query}"
    
    @error_handler
    def _retrieve_relevant_chunks(self, query, num_chunks=5):
        """
        Retrieve relevant chunks from the vector store based on the query.
        
        Args:
            query (str): Search query.
            num_chunks (int): Number of chunks to retrieve.
            
        Returns:
            str: Concatenated text from relevant chunks.
        """
        try:
            logger.debug(f"Searching for: {query}")
            
            # Retrieve documents
            docs = self.vector_store.similarity_search(query, k=num_chunks)
            
            # Concatenate content
            context = "\n\n".join([doc.page_content for doc in docs])
            
            logger.debug(f"Retrieved {len(docs)} chunks, total length: {len(context)} chars")
            
            return context
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            raise AnalysisError(f"Failed to retrieve chunks: {str(e)}")
    
    @error_handler
    def _process_with_llm(self, key_point, context):
        """
        Process the context with LLM to extract key point information.
        
        Args:
            key_point (str): The key point to extract.
            context (str): The context from relevant chunks.
            
        Returns:
            str: Extracted information about the key point.
        """
        try:
            # Create prompt template based on key point
            prompt_template = self._create_prompt_template(key_point)
            
            # Create LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template
            )
            
            # Run chain
            logger.debug(f"Running LLM chain for {key_point}")
            # Use {"context": context} as input dict instead of named parameter
            result = chain.invoke({"context": context})
            
            # Handle different return types in different LangChain versions
            if isinstance(result, dict):
                if "text" in result:
                    result = result["text"]
                elif "output" in result:
                    result = result["output"]
                elif isinstance(next(iter(result.values()), ""), str):
                    # Get the first string value if there's no known key
                    result = next(iter(result.values()))
            
            logger.debug(f"LLM extraction result length: {len(str(result))} chars")
            
            return str(result).strip()
        except Exception as e:
            logger.error(f"Error in LLM processing: {str(e)}")
            logger.info("Falling back to rule-based extraction")
            return self._process_with_fallback(key_point, context)
    
    @error_handler
    def _create_prompt_template(self, key_point):
        """
        Create a prompt template for the key point.
        
        Args:
            key_point (str): The key point to create a prompt for.
            
        Returns:
            PromptTemplate: Prompt template for the key point.
        """
        # Base template
        base_template = """
        You are a professional tender document analyzer. Your task is to extract accurate information 
        about {key_point} from the given tender document context.
        
        Context from tender document:
        {context}
        
        Extract all relevant information about {key_point} from the above context.
        Be specific, detailed, and accurate. Focus only on extracting factual information.
        Organize the information in a clear, structured format.
        If information is not available, state so clearly.
        
        {specific_instructions}
        
        Your detailed extraction about {key_point}:
        """
        
        # Specific instructions based on key point
        specific_instructions = {
            "Deadline": """
            For Deadline information, extract:
            - Submission deadline (exact date and time)
            - Pre-proposal meeting dates if any
            - Q&A submission deadlines
            - Evaluation timeline
            - Project start and end dates if mentioned
            List all dates chronologically with their corresponding events.
            """,
            
            "Project Requirement": """
            For Project Requirements, extract:
            - Core project objectives
            - Detailed scope of work
            - Technical specifications
            - Required deliverables
            - Any mandatory project phases or components
            - Special requirements or conditions
            Organize by categories and list all important requirements.
            """,
            
            "Cost": """
            For Cost information, extract:
            - Total budget or estimated cost if mentioned
            - Payment schedule and milestones
            - Payment terms and conditions
            - Budget constraints
            - Cost breakdown requirements
            - Financial guarantees or securities required
            Be precise about financial figures, percentages, and payment timelines.
            """,
            
            "Quality Checking": """
            For Quality Checking information, extract:
            - Quality control requirements
            - Testing procedures
            - Hardware specifications and quality standards
            - Software requirements and quality standards
            - Required certifications or compliance standards
            - Quality assurance documentation requirements
            - Inspection and acceptance criteria
            List all quality-related requirements systematically.
            """
        }
        
        # Get specific instructions for this key point
        instructions = specific_instructions.get(key_point, "Provide a detailed extraction of the information.")
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["context"],
            partial_variables={"key_point": key_point, "specific_instructions": instructions},
            template=base_template
        )
        
        return prompt 