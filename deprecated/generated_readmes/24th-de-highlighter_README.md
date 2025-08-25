<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

<img src="readmeai/assets/logos/purple.svg" width="30%" style="position: relative; top: 0; right: 0;" alt="Project Logo"/>

# 24TH-DE-HIGHLIGHTER

<em>Transforming data into actionable insights, effortlessly.</em>

<!-- BADGES -->
<!-- local repository, no metadata badges. -->

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Org-77AA99.svg?style=default&logo=Org&logoColor=white" alt="Org">
<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=default&logo=FastAPI&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/Gradle-02303A.svg?style=default&logo=Gradle&logoColor=white" alt="Gradle">
<img src="https://img.shields.io/badge/NumPy-013243.svg?style=default&logo=NumPy&logoColor=white" alt="NumPy">
<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=default&logo=Docker&logoColor=white" alt="Docker">
<img src="https://img.shields.io/badge/XML-005FAD.svg?style=default&logo=XML&logoColor=white" alt="XML">
<br>
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/bat-31369E.svg?style=default&logo=bat&logoColor=white" alt="bat">
<img src="https://img.shields.io/badge/pandas-150458.svg?style=default&logo=pandas&logoColor=white" alt="pandas">
<img src="https://img.shields.io/badge/Terraform-844FBA.svg?style=default&logo=Terraform&logoColor=white" alt="Terraform">
<img src="https://img.shields.io/badge/Apache-D22128.svg?style=default&logo=Apache&logoColor=white" alt="Apache">
<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=default&logo=YAML&logoColor=white" alt="YAML">

</div>
<br>

---

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
    - [Project Index](#project-index)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

**24th-de-highlighter** is a powerful developer tool designed to streamline data processing and enhance video management workflows. 

**Why 24th-de-highlighter?**

This project simplifies complex data handling and video processing tasks, enabling developers to focus on building innovative solutions. The core features include:

- 🎥 **Time Normalization:** Standardizes various time formats, enhancing data consistency for analysis.
- ☁️ **Infrastructure as Code:** Simplifies AWS deployment with defined configurations for security and scalability.
- 📊 **Real-time Data Processing:** Integrates Kafka and InfluxDB for efficient handling of streaming data.
- 🎬 **Video Management:** Facilitates video data extraction, processing, and storage in AWS S3.
- 🚀 **Automated Uploads:** Streamlines video uploads to YouTube using AWS Lambda, improving content management workflows.

---

## Features

|      | Component       | Details                              |
| :--- | :-------------- | :----------------------------------- |
| ⚙️  | **Architecture**  | <ul><li>Microservices-based design</li><li>Utilizes Docker for containerization</li><li>Supports multiple programming languages (Python, Java)</li></ul> |
| 🔩 | **Code Quality**  | <ul><li>Gradle and Python package management for dependency resolution</li><li>Consistent coding standards enforced via CI/CD tools</li><li>Logback for logging configuration</li></ul> |
| 📄 | **Documentation** | <ul><li>Comprehensive README and examples in `.env.example`</li><li>Docker documentation for setup and usage</li><li>Inline comments in code for clarity</li></ul> |
| 🔌 | **Integrations**  | <ul><li>Integrates with Kafka for streaming data</li><li>Uses FastAPI for building APIs</li><li>Supports InfluxDB for time-series data storage</li></ul> |
| 🧩 | **Modularity**    | <ul><li>Separation of concerns with distinct modules for video streaming, data processing, and highlighting</li><li>Reusable components across different services</li></ul> |
| 🧪 | **Testing**       | <ul><li>Unit tests defined in Gradle for Java components</li><li>Python tests managed via `pytest` in requirements.txt</li><li>CI/CD pipelines ensure tests are run on every commit</li></ul> |
| ⚡️  | **Performance**   | <ul><li>Optimized for real-time data processing</li><li>Efficient use of resources through Docker containers</li><li>Asynchronous processing with FastAPI and asyncio</li></ul> |
| 🛡️ | **Security**      | <ul><li>Environment variables managed via `.env.example` for sensitive data</li><li>Secure dependencies with `pip` and `gradle`</li><li>Regular updates to dependencies to mitigate vulnerabilities</li></ul> |
| 📦 | **Dependencies**  | <ul><li>Python dependencies listed in `requirements.txt`</li><li>Java dependencies managed via `build.gradle`</li><li>Docker dependencies specified in `docker-compose.yaml`</li></ul> |
| 🚀 | **Scalability**   | <ul><li>Horizontal scaling supported through Docker containers</li><li>Kafka integration allows for scalable message processing</li><li>Modular architecture facilitates independent scaling of components</li></ul> |
```

---

## Project Structure

```sh
└── 24th-de-highlighter/
    ├── README.md
    ├── assets
    ├── data
    ├── highlighter-sliding-window
    ├── influx
    ├── spark-streaming
    ├── terraform
    ├── timeframe
    ├── video-stream
    ├── video-upload
    └── youtube-live
```

### Project Index

<details open>
	<summary><b><code>24TH-DE-HIGHLIGHTER/</code></b></summary>
	<!-- __root__ Submodule -->
	<details>
		<summary><b>__root__</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ __root__</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
			</table>
		</blockquote>
	</details>
	<!-- timeframe Submodule -->
	<details>
		<summary><b>timeframe</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ timeframe</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/timeframe/normalize_time.py'>normalize_time.py</a></b></td>
					<td style='padding: 8px;'>- Mm:ss format<br>- This process enhances data consistency and usability, particularly for time-related analyses<br>- The resulting normalized data is then displayed and can be saved back into a CSV file, facilitating further processing or integration within the broader project architecture focused on data analysis and manipulation.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- terraform Submodule -->
	<details>
		<summary><b>terraform</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ terraform</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/terraform/main.tf'>main.tf</a></b></td>
					<td style='padding: 8px;'>- Defines infrastructure as code for deploying an AWS environment, including a security group and an application server<br>- It establishes necessary configurations for the AWS provider and specifies a virtual private cloud (VPC) integration<br>- The security group allows inbound traffic on specified ports, while the application server is provisioned with a designated Amazon Machine Image (AMI) and associated security settings, facilitating a secure and scalable deployment.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- influx Submodule -->
	<details>
		<summary><b>influx</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ influx</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/delete_bucket.py'>delete_bucket.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the deletion of specified buckets in an InfluxDB instance by utilizing the InfluxDB client and environment variables for configuration<br>- It checks for the existence of the target bucket and executes the deletion if found, ensuring efficient management of database resources within the overall project architecture<br>- This functionality supports streamlined data handling and maintenance in the broader context of the application.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/influxDB_range.py'>influxDB_range.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the extraction, processing, and uploading of video data from InfluxDB based on timestamps received from a Kafka stream<br>- It analyzes conversations around specified times, generates contextual insights using OpenAIs API, and manages video file conversion and storage in AWS S3<br>- This component plays a crucial role in the overall architecture by enabling real-time video content management and analysis.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/requirements.txt'>requirements.txt</a></b></td>
					<td style='padding: 8px;'>- Defines essential dependencies for the project, ensuring seamless integration with Confluent Kafka for data streaming, InfluxDB for time-series data storage, and Python Dotenv for environment variable management<br>- These components collectively facilitate efficient data handling and configuration management, forming a robust foundation for the overall architecture and enhancing the projects capability to process and analyze real-time data effectively.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/insert_text.py'>insert_text.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the insertion of text data into an InfluxDB database, enabling efficient storage and retrieval of time-series data<br>- By establishing a connection to the InfluxDB instance and utilizing the Write API, it captures and timestamps model output, ensuring that relevant information is systematically logged for further analysis within the broader project architecture<br>- This integration supports data-driven decision-making and enhances the overall functionality of the application.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/insert_binary.py'>insert_binary.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the ingestion of binary messages from a Kafka topic and stores them in InfluxDB<br>- By establishing a connection to both Kafka and InfluxDB, it processes incoming messages, encodes them, and timestamps them for accurate storage<br>- This integration enables real-time data monitoring and analysis, contributing to the overall architectures capability to handle streaming data efficiently.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/influxDB_video.py'>influxDB_video.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the extraction, decoding, and conversion of video data from InfluxDB into a usable format<br>- It retrieves video binary data, decodes it into a.ts file, converts the.ts file to.mp4 format, and uploads the resulting video to AWS S3<br>- This process integrates data handling and cloud storage, enhancing the overall functionality of the project by enabling video processing and distribution.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/read_binary.py'>read_binary.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the retrieval of time-series data from an InfluxDB instance, specifically targeting measurements related to video text<br>- By establishing a connection using environment variables for configuration, it executes a query to filter and sort data based on specified timestamps<br>- The output is formatted for easy consumption, enabling further analysis or integration within the broader project architecture.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/influx/delete_measurement.py'>delete_measurement.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the deletion of specific measurement data from an InfluxDB bucket, enabling efficient data management within the project<br>- By connecting to the InfluxDB instance using environment variables, it allows users to specify a measurement for removal across a defined time range, thereby ensuring that outdated or unnecessary data can be effectively purged from the system.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- video-stream Submodule -->
	<details>
		<summary><b>video-stream</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ video-stream</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/docker-compose.yaml'>docker-compose.yaml</a></b></td>
					<td style='padding: 8px;'>- Defines a Kafka broker service within the video-stream project architecture, facilitating real-time data streaming and messaging<br>- It configures essential parameters for communication, ensuring reliable message delivery and processing across distributed systems<br>- This service acts as a central component, enabling seamless interaction between various microservices and enhancing the overall functionality of the video streaming application.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/sdk-test.ipynb'>sdk-test.ipynb</a></b></td>
					<td style='padding: 8px;'>- Demonstrates the integration of AWS SQS for message handling within a video streaming context<br>- It facilitates sending, receiving, and deleting messages related to video data, while also managing timestamps for message processing<br>- This notebook serves as a practical guide for testing and validating the SQS interactions, ensuring efficient communication and data flow in the overall architecture of the video-streaming application.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/requirements.txt'>requirements.txt</a></b></td>
					<td style='padding: 8px;'>- Defines the dependencies required for the video-stream project, ensuring that all necessary libraries and packages are available for seamless functionality<br>- By specifying versions for each dependency, it facilitates a consistent development environment, enhances compatibility, and supports the overall architecture aimed at delivering a robust video streaming experience<br>- This foundational setup is crucial for maintaining the integrity and performance of the application.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/trigger_request.py'>trigger_request.py</a></b></td>
					<td style='padding: 8px;'>- Enqueues requests to an Amazon SQS queue, facilitating communication between an API Gateway and downstream processing services<br>- By parsing start and end timestamps from incoming requests, it ensures that relevant data is efficiently queued for further handling<br>- This functionality is essential for managing video processing tasks within the broader architecture of the project, enabling seamless integration and scalability.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/producer.py'>producer.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the streaming of data by producing messages to a Kafka topic, enabling real-time data processing within the video-stream architecture<br>- It establishes a connection to a Kafka broker, configures logging for monitoring message delivery, and iteratively sends a series of data messages while handling potential delivery errors<br>- This component plays a crucial role in ensuring seamless data flow in the overall system.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/sqs_trigger_task.py'>sqs_trigger_task.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the saving of video content to Amazon S3, triggered by messages from an SQS queue<br>- It processes video segments based on specified start and end timestamps, ensuring only relevant data is captured<br>- Upon successful processing, the video is converted to MP4 format and uploaded to a designated S3 bucket, while handling errors gracefully by logging them for further review.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-stream/main.py'>main.py</a></b></td>
					<td style='padding: 8px;'>- Streamlink Kafka Producer facilitates the capture and transmission of live video streams from platforms like YouTube to an Apache Kafka topic<br>- By reading the stream data for a specified duration and buffer size, it ensures efficient delivery to the messaging system, enabling real-time processing and analysis of video content within the broader architecture of the project.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- youtube-live Submodule -->
	<details>
		<summary><b>youtube-live</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ youtube-live</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/youtube-live/docker-compose.yaml'>docker-compose.yaml</a></b></td>
					<td style='padding: 8px;'>- Facilitates the deployment of the YouTube Live application using Docker Compose, streamlining the setup process for developers<br>- By defining the application service and its dependencies, it ensures a consistent environment for running the app, while also allowing for easy integration of chat functionalities through mounted volumes<br>- The specified YouTube URL serves as a default input for the live streaming feature.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/youtube-live/requirements.txt'>requirements.txt</a></b></td>
					<td style='padding: 8px;'>- Facilitates the management of dependencies essential for a YouTube live streaming application<br>- By incorporating libraries such as youtube-dl for video downloading, FastAPI for building the web framework, and Kafka for real-time data processing, it ensures seamless integration and functionality within the overall architecture, enabling efficient data handling and user interaction in a dynamic streaming environment.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/youtube-live/Dockerfile'>Dockerfile</a></b></td>
					<td style='padding: 8px;'>- Facilitates the deployment of a Python-based web application within a Docker container<br>- By establishing a working directory, installing necessary dependencies, and exposing port 80, it ensures a streamlined environment for running the application using Uvicorn<br>- This setup is integral to the overall architecture, enabling efficient development and deployment of the live streaming features of the project.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/youtube-live/app.py'>app.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates real-time streaming of YouTube live chat messages by connecting to a specified live video URL<br>- It captures chat data and sends timestamps to a Kafka topic, enabling further processing and analysis<br>- This integration enhances the overall architecture by allowing seamless communication between live chat interactions and data handling systems, thereby supporting dynamic content engagement and monitoring.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/youtube-live/.env.example'>.env.example</a></b></td>
					<td style='padding: 8px;'>- Defines environment variables necessary for configuring the application, specifically for integrating Google Cloud Platform and OpenAI services<br>- By providing placeholders for sensitive keys, it ensures secure management of credentials while facilitating seamless interaction with external APIs<br>- This setup is crucial for the overall functionality of the project, enabling features that rely on cloud services and AI capabilities.</td>
				</tr>
			</table>
			<!-- chat Submodule -->
			<details>
				<summary><b>chat</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ youtube-live.chat</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/youtube-live/chat/tmp.text'>tmp.text</a></b></td>
							<td style='padding: 8px;'>- Facilitates the management of temporary files within the upload folder for the YouTube Live project<br>- By allowing users to delete unnecessary files freely, it streamlines the workflow and optimizes storage usage<br>- This contributes to the overall efficiency of the codebase architecture, ensuring that the system remains organized and responsive during live streaming events.</td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<!-- highlighter-sliding-window Submodule -->
	<details>
		<summary><b>highlighter-sliding-window</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ highlighter-sliding-window</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/build.gradle'>build.gradle</a></b></td>
					<td style='padding: 8px;'>- Defines the build configuration for the highlighter-sliding-window project, establishing a foundation for a Spring Boot application that leverages Kafka Streams for real-time data processing<br>- It manages dependencies, including Spring Boot and Kafka libraries, ensuring compatibility and facilitating unit testing<br>- This setup enables seamless integration and deployment of microservices within a broader architecture focused on stream processing and data manipulation.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/gradlew.bat'>gradlew.bat</a></b></td>
					<td style='padding: 8px;'>- Facilitates the execution of Gradle tasks on Windows systems by providing a startup script tailored for the platform<br>- It ensures the correct Java environment is set up, allowing seamless integration with the overall project architecture<br>- This script plays a crucial role in managing dependencies and building the application, thereby enhancing the development workflow within the highlighter-sliding-window project.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/settings.gradle'>settings.gradle</a></b></td>
					<td style='padding: 8px;'>- Defines the root project name for the example application within the highlighter-sliding-window codebase<br>- This foundational setting establishes the identity of the project, facilitating organization and management of dependencies and modules throughout the architecture<br>- It plays a crucial role in ensuring that the build system recognizes and operates under the specified project name, contributing to the overall coherence of the development environment.</td>
				</tr>
			</table>
			<!-- src Submodule -->
			<details>
				<summary><b>src</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ highlighter-sliding-window.src</b></code>
					<!-- test Submodule -->
					<details>
						<summary><b>test</b></summary>
						<blockquote>
							<div class='directory-path' style='padding: 8px 0; color: #666;'>
								<code><b>⦿ highlighter-sliding-window.src.test</b></code>
							<!-- java Submodule -->
							<details>
								<summary><b>java</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ highlighter-sliding-window.src.test.java</b></code>
									<!-- kafkastreams Submodule -->
									<details>
										<summary><b>kafkastreams</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ highlighter-sliding-window.src.test.java.kafkastreams</b></code>
											<!-- example Submodule -->
											<details>
												<summary><b>example</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ highlighter-sliding-window.src.test.java.kafkastreams.example</b></code>
													<table style='width: 100%; border-collapse: collapse;'>
													<thead>
														<tr style='background-color: #f8f9fa;'>
															<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
															<th style='text-align: left; padding: 8px;'>Summary</th>
														</tr>
													</thead>
														<tr style='border-bottom: 1px solid #eee;'>
															<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/src/test/java/kafkastreams/example/ExampleApplicationTests.java'>ExampleApplicationTests.java</a></b></td>
															<td style='padding: 8px;'>- Facilitates the testing of the application context within the Kafka Streams project<br>- By ensuring that the Spring Boot application loads correctly, it verifies the foundational setup of the codebase, contributing to the overall reliability and stability of the application<br>- This testing component plays a crucial role in maintaining code quality and supporting further development efforts.</td>
														</tr>
													</table>
												</blockquote>
											</details>
										</blockquote>
									</details>
								</blockquote>
							</details>
						</blockquote>
					</details>
					<!-- main Submodule -->
					<details>
						<summary><b>main</b></summary>
						<blockquote>
							<div class='directory-path' style='padding: 8px 0; color: #666;'>
								<code><b>⦿ highlighter-sliding-window.src.main</b></code>
							<!-- resources Submodule -->
							<details>
								<summary><b>resources</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ highlighter-sliding-window.src.main.resources</b></code>
									<table style='width: 100%; border-collapse: collapse;'>
									<thead>
										<tr style='background-color: #f8f9fa;'>
											<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
											<th style='text-align: left; padding: 8px;'>Summary</th>
										</tr>
									</thead>
										<tr style='border-bottom: 1px solid #eee;'>
											<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/src/main/resources/logback.xml'>logback.xml</a></b></td>
											<td style='padding: 8px;'>- Configures logging for the highlighter-sliding-window project, establishing a clear output format for log messages and setting appropriate log levels for different components<br>- By directing logs to the console and filtering verbosity for specific libraries, it enhances the observability of the application, facilitating easier debugging and monitoring of the Kafka Streams processing within the overall architecture.</td>
										</tr>
									</table>
								</blockquote>
							</details>
							<!-- java Submodule -->
							<details>
								<summary><b>java</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ highlighter-sliding-window.src.main.java</b></code>
									<!-- kafkastreams Submodule -->
									<details>
										<summary><b>kafkastreams</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ highlighter-sliding-window.src.main.java.kafkastreams</b></code>
											<!-- example Submodule -->
											<details>
												<summary><b>example</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ highlighter-sliding-window.src.main.java.kafkastreams.example</b></code>
													<!-- KStream Submodule -->
													<details>
														<summary><b>KStream</b></summary>
														<blockquote>
															<div class='directory-path' style='padding: 8px 0; color: #666;'>
																<code><b>⦿ highlighter-sliding-window.src.main.java.kafkastreams.example.KStream</b></code>
															<table style='width: 100%; border-collapse: collapse;'>
															<thead>
																<tr style='background-color: #f8f9fa;'>
																	<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
																	<th style='text-align: left; padding: 8px;'>Summary</th>
																</tr>
															</thead>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/src/main/java/kafkastreams/example/KStream/Consumer.java'>Consumer.java</a></b></td>
																	<td style='padding: 8px;'>- Kafka consumer implementation facilitates the consumption of messages from a specified Kafka topic, enabling real-time data processing within the application<br>- It initializes a consumer with appropriate configurations, subscribes to the topic, and continuously polls for incoming records, logging key details for monitoring<br>- This component plays a crucial role in the overall architecture by ensuring seamless data flow and processing in the streaming application.</td>
																</tr>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/src/main/java/kafkastreams/example/KStream/Producer.java'>Producer.java</a></b></td>
																	<td style='padding: 8px;'>- Facilitates the production of messages to a Kafka topic, enabling real-time data streaming within the application<br>- It initializes a Kafka producer, reads input from the user, and sends key-value pairs to the specified topic<br>- This component plays a crucial role in the overall architecture by ensuring seamless data flow and integration with Kafka, supporting the projects streaming capabilities.</td>
																</tr>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/highlighter-sliding-window/src/main/java/kafkastreams/example/KStream/KStreams.java'>KStreams.java</a></b></td>
																	<td style='padding: 8px;'>- KStreams facilitates real-time processing of timestamped data streams using Apache Kafka<br>- It ingests data from a specified source, converts timestamps to epoch format, and counts occurrences within defined time windows<br>- The application identifies when counts exceed a specified threshold, logging relevant information and forwarding results to a designated sink<br>- This architecture supports efficient monitoring and analysis of time-based events in streaming data.</td>
																</tr>
															</table>
														</blockquote>
													</details>
												</blockquote>
											</details>
										</blockquote>
									</details>
								</blockquote>
							</details>
						</blockquote>
					</details>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<!-- video-upload Submodule -->
	<details>
		<summary><b>video-upload</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ video-upload</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/video-upload/lambda_videoUpload.py'>lambda_videoUpload.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates the upload of videos to YouTube by integrating AWS Lambda with the YouTube API<br>- It retrieves necessary authentication credentials from AWS Secrets Manager, processes video files stored in S3, and manages the upload process, including error handling and retries<br>- This component plays a crucial role in automating video uploads, enhancing the overall functionality of the project by streamlining content management workflows.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- spark-streaming Submodule -->
	<details>
		<summary><b>spark-streaming</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ spark-streaming</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/spark-streaming/requirements.txt'>requirements.txt</a></b></td>
					<td style='padding: 8px;'>- Defines essential dependencies for the Spark Streaming project, ensuring seamless integration and functionality<br>- By including libraries such as PySpark, NumPy, and Pandas, it facilitates data processing and analysis<br>- Additionally, the inclusion of InfluxDB client and OpenAI Whisper enhances capabilities for time-series data management and advanced audio processing, respectively, contributing to a robust architecture for real-time data applications.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/24th-de-highlighter/spark-streaming/spark-batch.py'>spark-batch.py</a></b></td>
					<td style='padding: 8px;'>- Facilitates real-time processing of video streams by integrating Apache Spark with Kafka and InfluxDB<br>- It captures video byte arrays, aggregates them into 30-second windows, converts them to MP4 format, and performs speech-to-text transcription using the Whisper model<br>- The transcribed text, along with timestamps, is then stored in InfluxDB and saved as JSON files for further analysis, enabling efficient data handling and retrieval.</td>
				</tr>
			</table>
		</blockquote>
	</details>
</details>

---

## Getting Started

### Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python
- **Package Manager:** Pip, Gradle
- **Container Runtime:** Docker

### Installation

Build 24th-de-highlighter from the source and intsall dependencies:

1. **Clone the repository:**

    ```sh
    ❯ git clone ../24th-de-highlighter
    ```

2. **Navigate to the project directory:**

    ```sh
    ❯ cd 24th-de-highlighter
    ```

3. **Install the dependencies:**

<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![docker][docker-shield]][docker-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [docker-shield]: https://img.shields.io/badge/Docker-2CA5E0.svg?style={badge_style}&logo=docker&logoColor=white -->
	<!-- [docker-link]: https://www.docker.com/ -->

	**Using [docker](https://www.docker.com/):**

	```sh
	❯ docker build -t temp_github_repos/24th-de-highlighter .
	```
<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![pip][pip-shield]][pip-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [pip-shield]: https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white -->
	<!-- [pip-link]: https://pypi.org/project/pip/ -->

	**Using [pip](https://pypi.org/project/pip/):**

	```sh
	❯ pip install -r influx/requirements.txt, video-stream/requirements.txt, youtube-live/requirements.txt, spark-streaming/requirements.txt
	```
<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![gradle][gradle-shield]][gradle-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [gradle-shield]: None -->
	<!-- [gradle-link]: None -->

	**Using [gradle](None):**

	```sh
	❯ echo 'INSERT-INSTALL-COMMAND-HERE'
	```

### Usage

Run the project with:

**Using [docker](https://www.docker.com/):**
```sh
docker run -it {image_name}
```
**Using [pip](https://pypi.org/project/pip/):**
```sh
python {entrypoint}
```
**Using [gradle](None):**
```sh
echo 'INSERT-RUN-COMMAND-HERE'
```

### Testing

24th-de-highlighter uses the {__test_framework__} test framework. Run the test suite with:

**Using [pip](https://pypi.org/project/pip/):**
```sh
pytest
```
**Using [gradle](None):**
```sh
echo 'INSERT-TEST-COMMAND-HERE'
```

---

## Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

## Contributing

- **💬 [Join the Discussions](https://LOCAL/temp_github_repos/24th-de-highlighter/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://LOCAL/temp_github_repos/24th-de-highlighter/issues)**: Submit bugs found or log feature requests for the `24th-de-highlighter` project.
- **💡 [Submit Pull Requests](https://LOCAL/temp_github_repos/24th-de-highlighter/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your LOCAL account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone temp_github_repos/24th-de-highlighter
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to LOCAL**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://LOCAL{/temp_github_repos/24th-de-highlighter/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=temp_github_repos/24th-de-highlighter">
   </a>
</p>
</details>

---

## License

24th-de-highlighter is protected under the [LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

## Acknowledgments

- Credit `contributors`, `inspiration`, `references`, etc.

<div align="right">

[![][back-to-top]](#top)

</div>


[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square


---
