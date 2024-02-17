# Welcome to mixa-ai

## Introduction / Overview

Hi! I am Isaac Johnson and this is my capstone project mixa-ai! Mixa-ai is a cloud based and AI power video editing website. Integrating the latest from vision, language, and embedding AI to create a streamlined video editing experience. This document will go over the more technical details of the project, so buckle up! For a less technical information please visit the informational website here http://www.mixa-ai.com.

## Frameworks and Cloud Providers

- ### AWS

  <details>
    <summary>Explanation</summary>
    AWS served as the cloud provider for this project. It provided critical services like Cognito Users, Lambdas, API Gateways, WebSocket Gateways, Rekognition Vision AI, and Media Covert. I also chose this to learn the platform better as it had intrigued me before the project. It was used in conjunction with Serverless Framework.
  </details>

- ### Serverless Framework

  <details>
    <summary>Explanation</summary>
    Serverless Framework is an infrastructure as code framework for cloud platforms that allows cloud services to be defined as a config and can easily deploy and version your architecture. I chose this one as apposed to other popular IaC frameworks for it's capabilities of quickly setting up serverless architecture. I think if I where to do this project over I would look into the benefits of other IaC as I didn't weigh any other one before the project.
  </details>

- ### Next.js React

  <details>
    <summary>Explanation</summary>
    Next.js React was used for the frontend web framework. Next.js provides a lot of utilities on top of React, making development smoother and a lot less boiler plate. Next.js also integrates with AWS Amplify which was used for hosting the website
  </details>

- ### AWS Amplify
  <details>
    <summary>Explanation</summary>
    I mostly used AWS Amplify to integrate my Cognito auth and API Gateways into the frontend. It provided a nice frontend package for the quick implantation of both of those services.
  </details>

## Programming Languages

- ### Python

  Python is the langues chosen for the backend of the project. I chose it for it's development and variety of well supported packages. In hindsight I think this was the right decision as a faster backend development speed allowed me to make a big pivot in the middle of project.

- ### Typescript
  Typescript was used for the in the React frontend of the project. Typescript was chosen for it's type safety and again for it's host of well supported packages. I find type safety in React to helpful and speed up development by preventing many small bugs before they even happen.

## Tools

- ### OpenAI

  OpenAI's API was used for it's GPT-4 language model and it's embedding model. This was used in conjunction with Pinecone DB to create a RAG model from the analyzed video's data.

- ### Pinecone DB

  Pinecone provided a cloud vector database that provide metadata and k-mean queries making the process of finding relevant data for user text quires much easier

### Changes to the tools

Midway through the project OpenAI introduced it's Assistants. I am using the Python package LangChain in the project currently. While this package made development a little easy with it's tools for embeddings and Pinecone, it has many issues and the main problems it was solving where solved by in introduction of Assistants. In the future, I would want to migrate to using Assistants.
