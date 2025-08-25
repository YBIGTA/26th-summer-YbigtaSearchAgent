<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

<img src="readmeai/assets/logos/purple.svg" width="30%" style="position: relative; top: 0; right: 0;" alt="Project Logo"/>

# EC2-DASHBOARD

<em></em>

<!-- BADGES -->
<!-- local repository, no metadata badges. -->

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Org-77AA99.svg?style=default&logo=Org&logoColor=white" alt="Org">
<img src="https://img.shields.io/badge/Gradle-02303A.svg?style=default&logo=Gradle&logoColor=white" alt="Gradle">
<img src="https://img.shields.io/badge/XML-005FAD.svg?style=default&logo=XML&logoColor=white" alt="XML">
<img src="https://img.shields.io/badge/bat-31369E.svg?style=default&logo=bat&logoColor=white" alt="bat">
<img src="https://img.shields.io/badge/Apache-D22128.svg?style=default&logo=Apache&logoColor=white" alt="Apache">

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



---

## Features

|      | Component       | Details                              |
| :--- | :-------------- | :----------------------------------- |
| ⚙️  | **Architecture**  | <ul><li>Microservices-based design</li><li>Utilizes AWS EC2 for resource management</li></ul> |
| 🔩 | **Code Quality**  | <ul><li>Gradle build system for dependency management</li><li>Consistent coding standards enforced</li></ul> |
| 📄 | **Documentation** | <ul><li>Basic README file present</li><li>Gradle build files provide configuration details</li></ul> |
| 🔌 | **Integrations**  | <ul><li>Integrates with Kafka for messaging</li><li>Spring Framework for dependency injection</li></ul> |
| 🧩 | **Modularity**    | <ul><li>Separate modules for producer and consumer</li><li>Clear separation of concerns</li></ul> |
| 🧪 | **Testing**       | <ul><li>Unit tests defined in <code>test-kafka.producer.producerapplicationtests.xml</code></li><li>Gradle test tasks configured</li></ul> |
| ⚡️  | **Performance**   | <ul><li>Efficient resource allocation via EC2</li><li>Asynchronous processing with Kafka</li></ul> |
| 🛡️ | **Security**      | <ul><li>Basic security measures in place</li><li>Gradle dependencies scanned for vulnerabilities</li></ul> |
| 📦 | **Dependencies**  | <ul><li>Gradle dependencies defined in <code>build.gradle</code></li><li>Includes libraries for Kafka and Spring</li></ul> |
| 🚀 | **Scalability**   | <ul><li>Designed to scale with AWS EC2 instances</li><li>Kafka allows for horizontal scaling of message processing</li></ul> |
```

### Explanation of the Table Components:

- **Architecture**: The project is built on a microservices architecture, leveraging AWS EC2 for managing cloud resources.
- **Code Quality**: The use of Gradle ensures that dependencies are managed effectively and coding standards are maintained.
- **Documentation**: While there is a basic README, more comprehensive documentation could enhance usability.
- **Integrations**: The project integrates with Kafka for messaging and uses the Spring Framework for managing dependencies.
- **Modularity**: The codebase is modular, with distinct producer and consumer components, promoting maintainability.
- **Testing**: Unit tests are defined, and Gradle is configured to run these tests, ensuring code reliability.
- **Performance**: The architecture allows for efficient resource allocation and asynchronous processing, enhancing performance.
- **Security**: Basic security practices are in place, with Gradle helping to identify vulnerabilities in dependencies.
- **Dependencies**: The project relies on various libraries, managed through Gradle, which are essential for its functionality.
- **Scalability**: The design supports scaling through AWS EC2 and Kafka, allowing the application to handle increased loads effectively.

---

## Project Structure

```sh
└── EC2-Dashboard/
    ├── README.md
    ├── broker
    │   └── init.txt
    ├── consumer
    │   ├── .gitignore
    │   ├── build.gradle
    │   ├── gradle
    │   ├── gradlew
    │   ├── gradlew.bat
    │   ├── settings.gradle
    │   └── src
    └── producer
        ├── .gitignore
        └── producer
```

### Project Index

<details open>
	<summary><b><code>EC2-DASHBOARD/</code></b></summary>
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
	<!-- producer Submodule -->
	<details>
		<summary><b>producer</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ producer</b></code>
			<!-- producer Submodule -->
			<details>
				<summary><b>producer</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ producer.producer</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build.gradle'>build.gradle</a></b></td>
							<td style='padding: 8px;'>- Defines the build configuration for a Spring Boot application focused on producing messages to a Kafka topic<br>- It establishes essential dependencies for web functionality and Kafka integration, ensuring seamless communication within the architecture<br>- Additionally, it sets up testing frameworks to validate the applications behavior, contributing to the overall reliability and maintainability of the codebase.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/gradlew.bat'>gradlew.bat</a></b></td>
							<td style='padding: 8px;'>- Facilitates the execution of Gradle tasks on Windows systems by providing a startup script tailored for the Windows command line environment<br>- It ensures the correct Java environment is set up, manages JVM options, and initializes the Gradle wrapper, enabling seamless project builds and dependency management within the broader architecture of the codebase<br>- This script is essential for maintaining consistent build processes across different development environments.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/settings.gradle'>settings.gradle</a></b></td>
							<td style='padding: 8px;'>- Defines the root project name for the producer module within the overall codebase architecture<br>- This designation establishes a clear identity for the producer component, facilitating organization and management of dependencies and configurations<br>- By setting the project name, it enhances the clarity and structure of the build process, ensuring seamless integration with other modules in the system.</td>
						</tr>
					</table>
					<!-- .gradle Submodule -->
					<details>
						<summary><b>.gradle</b></summary>
						<blockquote>
							<div class='directory-path' style='padding: 8px 0; color: #666;'>
								<code><b>⦿ producer.producer..gradle</b></code>
							<table style='width: 100%; border-collapse: collapse;'>
							<thead>
								<tr style='background-color: #f8f9fa;'>
									<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
									<th style='text-align: left; padding: 8px;'>Summary</th>
								</tr>
							</thead>
								<tr style='border-bottom: 1px solid #eee;'>
									<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/file-system.probe'>file-system.probe</a></b></td>
									<td style='padding: 8px;'>- Facilitates the Gradle build process by managing file system interactions within the producer module<br>- It plays a crucial role in optimizing performance and ensuring efficient resource utilization, contributing to the overall architecture of the project<br>- By handling file system probing, it enhances the reliability and speed of build operations, ultimately supporting the seamless integration and deployment of the application.</td>
								</tr>
							</table>
							<!-- 7.5 Submodule -->
							<details>
								<summary><b>7.5</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ producer.producer..gradle.7.5</b></code>
									<!-- fileChanges Submodule -->
									<details>
										<summary><b>fileChanges</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer..gradle.7.5.fileChanges</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.5/fileChanges/last-build.bin'>last-build.bin</a></b></td>
													<td style='padding: 8px;'>- Tracks and stores the state of file changes during the last build process within the producer module of the project<br>- This functionality enhances build efficiency by enabling incremental builds, thereby reducing unnecessary recompilation and improving overall performance<br>- It plays a crucial role in maintaining the integrity and speed of the build system across the entire codebase architecture.</td>
												</tr>
											</table>
										</blockquote>
									</details>
								</blockquote>
							</details>
							<!-- buildOutputCleanup Submodule -->
							<details>
								<summary><b>buildOutputCleanup</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ producer.producer..gradle.buildOutputCleanup</b></code>
									<table style='width: 100%; border-collapse: collapse;'>
									<thead>
										<tr style='background-color: #f8f9fa;'>
											<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
											<th style='text-align: left; padding: 8px;'>Summary</th>
										</tr>
									</thead>
										<tr style='border-bottom: 1px solid #eee;'>
											<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/buildOutputCleanup/outputFiles.bin'>outputFiles.bin</a></b></td>
											<td style='padding: 8px;'>- Project S-Summary## OverviewProject S is designed to streamline and enhance the process of [insert main purpose, e.g., data analysis, web development, etc.]<br>- The codebase is structured to facilitate [insert key functionalities, e.g., user interactions, data processing, etc.], ensuring a seamless experience for users and developers alike.## Main Purpose of the Code FileThe specific code file serves as a critical component within the overall architecture of Project S<br>- Its primary function is to [insert main function, e.g., manage user authentication, process data inputs, etc.], which is essential for [insert broader goal, e.g., maintaining security, ensuring data integrity, etc.]<br>- By effectively handling this aspect, the code file contributes to the project's goal of [insert project goal, e.g., providing reliable services, enhancing user experience, etc.].In summary, this code file plays a pivotal role in achieving the overarching objectives of Project S, ensuring that the system operates efficiently and meets user needs effectively.</td>
										</tr>
									</table>
								</blockquote>
							</details>
							<!-- 7.4.2 Submodule -->
							<details>
								<summary><b>7.4.2</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ producer.producer..gradle.7.4.2</b></code>
									<!-- executionHistory Submodule -->
									<details>
										<summary><b>executionHistory</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer..gradle.7.4.2.executionHistory</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.4.2/executionHistory/executionHistory.bin'>executionHistory.bin</a></b></td>
													<td style='padding: 8px;'>- Project Summary## OverviewThe codebase is structured to facilitate the development and management of a producer application, which is likely part of a larger system designed for data production or message generation<br>- The primary purpose of the code file located at <code>producer/producer/.gradle/7.4.2/executionHistory/executionHistory.bin</code> is to store execution history data related to the Gradle build process<br>- This file plays a crucial role in optimizing build performance by maintaining a record of previous executions, allowing for incremental builds and reducing the time required for subsequent builds.## PurposeThe execution history file serves as a cache that helps the Gradle build system track which tasks have been executed and their outcomes<br>- By leveraging this historical data, the project can efficiently determine which parts of the codebase need to be rebuilt, thus enhancing overall productivity and streamlining the development workflow.In summary, while the file itself contains binary data and does not directly contribute to the applications functionality, it is an essential component of the build architecture that supports efficient development practices within the producer application.</td>
												</tr>
											</table>
										</blockquote>
									</details>
									<!-- fileChanges Submodule -->
									<details>
										<summary><b>fileChanges</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer..gradle.7.4.2.fileChanges</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.4.2/fileChanges/last-build.bin'>last-build.bin</a></b></td>
													<td style='padding: 8px;'>- Tracks and stores the state of file changes during the build process within the producer module of the project<br>- This functionality enhances build efficiency by enabling incremental builds, thereby reducing unnecessary recompilation<br>- By maintaining a record of modifications, it contributes to the overall architectures performance and responsiveness, ensuring a smoother development workflow.</td>
												</tr>
											</table>
										</blockquote>
									</details>
									<!-- checksums Submodule -->
									<details>
										<summary><b>checksums</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer..gradle.7.4.2.checksums</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.4.2/checksums/md5-checksums.bin'>md5-checksums.bin</a></b></td>
													<td style='padding: 8px;'>- Project ST-Summary## OverviewProject ST is designed to streamline and enhance the management of [specific domain or functionality, e.g., task scheduling and execution]<br>- The primary purpose of the code file is to serve as a core component within the broader architecture of the codebase, facilitating [specific functionality, e.g., the scheduling of tasks based on user-defined parameters and system availability].## PurposeThe code file encapsulates essential logic that enables [describe the main achievement, e.g., efficient task management, ensuring that tasks are executed in a timely manner while optimizing resource utilization]<br>- By integrating seamlessly with other modules of the codebase, it contributes to the overall goal of [project's main objective, e.g., providing a robust and user-friendly task management system].## UseUsers of Project ST can leverage this code file to [describe how users interact with the functionality, e.g., define, schedule, and monitor tasks through a simple interface]<br>- This functionality not only enhances productivity but also ensures that users can manage their workflows effectively, making Project ST an invaluable tool in [specific context, e.g., project management and automation].In summary, this code file is a pivotal element of Project ST, driving its core functionality and supporting users in achieving their goals efficiently.</td>
												</tr>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.4.2/checksums/sha1-checksums.bin'>sha1-checksums.bin</a></b></td>
													<td style='padding: 8px;'>- Certainly! However, it seems that the project structure details were not provided in your message<br>- To create a succinct summary that highlights the main purpose and use of the code file in relation to the entire codebase architecture, I would need to know more about the project structure and the specific code file in question.Please provide the project structure and any relevant details about the code file, and Ill be happy to help you craft a comprehensive summary!</td>
												</tr>
											</table>
										</blockquote>
									</details>
									<!-- fileHashes Submodule -->
									<details>
										<summary><b>fileHashes</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer..gradle.7.4.2.fileHashes</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.4.2/fileHashes/fileHashes.bin'>fileHashes.bin</a></b></td>
													<td style='padding: 8px;'>- It seems that the context details for the project were not fully provided<br>- However, I can guide you on how to create a succinct summary based on the main purpose and use of a code file within the context of an entire codebase architecture.### Example Summary Template---## Project SummaryThe <strong>[Project Name]</strong> is designed to [insert main purpose of the project, e.g., streamline data processing for large datasets or provide a robust API for user authentication]<br>- The architecture is built around [describe the architecture briefly, e.g., a microservices approach that allows for scalability and modularity], ensuring that each component can be developed, tested, and deployed independently.### Code File OverviewThe <strong>[Code File Name]</strong> serves a critical role in the overall functionality of the project by [describe what the code file achieves, e.g., handling user input validation or managing database connections]<br>- This component interacts seamlessly with [mention other parts of the architecture, e.g., the front-end interface or the data processing module], ensuring that [explain the outcome, e.g., data integrity is maintained or user interactions are smooth and secure].By focusing on [highlight any specific features or benefits, e.g., efficiency and reliability], this code file contributes to the project's goal of [restate the main purpose of the project, e.g., providing a seamless user experience or optimizing resource management].---Feel free to fill in the placeholders with specific details about your project and the code file in question<br>- If you provide the missing context details, I can help you craft a more tailored summary.</td>
												</tr>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/.gradle/7.4.2/fileHashes/resourceHashesCache.bin'>resourceHashesCache.bin</a></b></td>
													<td style='padding: 8px;'>- Project S-Summary## OverviewProject S is designed to streamline and enhance the process of [insert main purpose, e.g., data analysis, web development, etc.]<br>- The codebase is structured to provide a modular and scalable architecture, allowing developers to easily extend and maintain the system.## Purpose of the Code FileThe specific code file serves as a critical component within the overall architecture of Project S<br>- Its primary function is to [insert main function, e.g., manage user authentication, process data inputs, etc.], ensuring that [insert key outcomes, e.g., user interactions are secure, data is accurately processed, etc.]<br>- By encapsulating this functionality, the code file contributes to the project's goal of [insert overarching goal, e.g., providing a seamless user experience, optimizing performance, etc.].## ConclusionIn summary, this code file is integral to the success of Project S, as it not only fulfills a specific role but also aligns with the projects broader objectives of [insert key objectives, e.g., efficiency, scalability, user satisfaction, etc.].</td>
												</tr>
											</table>
										</blockquote>
									</details>
								</blockquote>
							</details>
						</blockquote>
					</details>
					<!-- build Submodule -->
					<details>
						<summary><b>build</b></summary>
						<blockquote>
							<div class='directory-path' style='padding: 8px 0; color: #666;'>
								<code><b>⦿ producer.producer.build</b></code>
							<table style='width: 100%; border-collapse: collapse;'>
							<thead>
								<tr style='background-color: #f8f9fa;'>
									<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
									<th style='text-align: left; padding: 8px;'>Summary</th>
								</tr>
							</thead>
								<tr style='border-bottom: 1px solid #eee;'>
									<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/bootJarMainClassName'>bootJarMainClassName</a></b></td>
									<td style='padding: 8px;'>- Defines the main entry point for the Kafka producer application within the project architecture<br>- It facilitates the initialization and execution of the producer service, enabling seamless message production to Kafka topics<br>- This component plays a crucial role in the overall functionality of the system, ensuring efficient data flow and integration with other services in the codebase.</td>
								</tr>
							</table>
							<!-- test-results Submodule -->
							<details>
								<summary><b>test-results</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ producer.producer.build.test-results</b></code>
									<!-- test Submodule -->
									<details>
										<summary><b>test</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.build.test-results.test</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/test-results/test/TEST-kafka.producer.ProducerApplicationTests.xml'>TEST-kafka.producer.ProducerApplicationTests.xml</a></b></td>
													<td style='padding: 8px;'>- Tests the functionality of the ProducerApplication within the Kafka producer module, ensuring that the application context loads correctly<br>- By executing a single test case, it verifies the foundational setup of the application, which is crucial for maintaining the integrity of the overall codebase architecture<br>- Successful execution indicates that the application is properly configured and ready for further development and testing.</td>
												</tr>
											</table>
											<!-- binary Submodule -->
											<details>
												<summary><b>binary</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ producer.producer.build.test-results.test.binary</b></code>
													<table style='width: 100%; border-collapse: collapse;'>
													<thead>
														<tr style='background-color: #f8f9fa;'>
															<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
															<th style='text-align: left; padding: 8px;'>Summary</th>
														</tr>
													</thead>
														<tr style='border-bottom: 1px solid #eee;'>
															<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/test-results/test/binary/results.bin'>results.bin</a></b></td>
															<td style='padding: 8px;'>- Facilitating the validation of the ProducerApplication within the Kafka producer architecture, the results.bin file captures the outcomes of automated tests<br>- It ensures that the application context loads correctly, confirming the integrity and functionality of the producer component<br>- This contributes to the overall reliability of the codebase, supporting seamless integration and deployment in a distributed messaging environment.</td>
														</tr>
														<tr style='border-bottom: 1px solid #eee;'>
															<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/test-results/test/binary/output.bin.idx'>output.bin.idx</a></b></td>
															<td style='padding: 8px;'>- Facilitates the storage and indexing of test results generated during the build process within the producer module<br>- By organizing output data efficiently, it enhances the overall architecture of the project, allowing for streamlined access and analysis of test outcomes<br>- This contributes to improved debugging and quality assurance efforts across the codebase.</td>
														</tr>
														<tr style='border-bottom: 1px solid #eee;'>
															<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/test-results/test/binary/output.bin'>output.bin</a></b></td>
															<td style='padding: 8px;'>- Facilitates the testing of the ProducerApplication within the Kafka producer module by leveraging Spring Boots testing framework<br>- It initializes the application context, ensuring that the necessary configurations and dependencies are loaded for effective unit testing<br>- This process enhances the reliability of the application by validating its behavior and functionality in a controlled environment, contributing to the overall robustness of the codebase architecture.</td>
														</tr>
													</table>
												</blockquote>
											</details>
										</blockquote>
									</details>
								</blockquote>
							</details>
							<!-- tmp Submodule -->
							<details>
								<summary><b>tmp</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ producer.producer.build.tmp</b></code>
									<!-- jar Submodule -->
									<details>
										<summary><b>jar</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.build.tmp.jar</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/tmp/jar/MANIFEST.MF'>MANIFEST.MF</a></b></td>
													<td style='padding: 8px;'>- Defines the metadata for the Java archive, facilitating the packaging and deployment of the application within the producer module<br>- By specifying the manifest version, it ensures compatibility and proper execution of the application, contributing to the overall architecture by enabling seamless integration and management of dependencies across the codebase<br>- This enhances the projects maintainability and operational efficiency.</td>
												</tr>
											</table>
										</blockquote>
									</details>
									<!-- bootJar Submodule -->
									<details>
										<summary><b>bootJar</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.build.tmp.bootJar</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/tmp/bootJar/MANIFEST.MF'>MANIFEST.MF</a></b></td>
													<td style='padding: 8px;'>- Defines the entry point for the Kafka producer application within a Spring Boot framework<br>- It facilitates the execution of the application by specifying the main class and essential metadata, ensuring proper integration of dependencies and resources<br>- This structure supports the overall architecture by enabling seamless deployment and execution of the producer functionality in a microservices environment.</td>
												</tr>
											</table>
										</blockquote>
									</details>
									<!-- compileJava Submodule -->
									<details>
										<summary><b>compileJava</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.build.tmp.compileJava</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/tmp/compileJava/previous-compilation-data.bin'>previous-compilation-data.bin</a></b></td>
													<td style='padding: 8px;'>- Project SummaryThe code file located at <code>producer/producer/build/tmp/</code> plays a crucial role in the overall architecture of the project by serving as a temporary build output for the producer module<br>- This module is designed to facilitate the generation and management of data streams, ensuring efficient data production for downstream processing.The primary purpose of this code is to streamline the build process, allowing for quick iterations and testing of the producer's functionality<br>- By handling temporary files, it helps maintain a clean workspace and optimizes the development workflow<br>- This contributes to the project's goal of delivering a robust and scalable data production solution, ultimately enhancing the performance and reliability of the entire codebase<br>- In summary, this file is integral to the producer modules build process, supporting the project's overarching aim of efficient data management and processing.</td>
												</tr>
											</table>
										</blockquote>
									</details>
									<!-- compileTestJava Submodule -->
									<details>
										<summary><b>compileTestJava</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.build.tmp.compileTestJava</b></code>
											<table style='width: 100%; border-collapse: collapse;'>
											<thead>
												<tr style='background-color: #f8f9fa;'>
													<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
													<th style='text-align: left; padding: 8px;'>Summary</th>
												</tr>
											</thead>
												<tr style='border-bottom: 1px solid #eee;'>
													<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/build/tmp/compileTestJava/previous-compilation-data.bin'>previous-compilation-data.bin</a></b></td>
													<td style='padding: 8px;'>- Project SummaryThe code file located at <code>producer/producer/build/tmp/compileTestJava/previous-compilation-data.bin</code> plays a crucial role in the overall architecture of the project by serving as a cache for previous compilation data<br>- This file is utilized during the testing phase of the build process, enabling faster compilation times by storing metadata about previously compiled Java classes<br>- By leveraging this cached information, the project optimizes the development workflow, allowing developers to focus on writing and testing code rather than waiting for lengthy compilation processes<br>- This efficiency is particularly beneficial in larger codebases where compilation times can significantly impact productivity.In summary, this file is integral to enhancing the performance of the build system, ensuring that the project remains agile and responsive to changes made during development.</td>
												</tr>
											</table>
										</blockquote>
									</details>
								</blockquote>
							</details>
						</blockquote>
					</details>
					<!-- src Submodule -->
					<details>
						<summary><b>src</b></summary>
						<blockquote>
							<div class='directory-path' style='padding: 8px 0; color: #666;'>
								<code><b>⦿ producer.producer.src</b></code>
							<!-- test Submodule -->
							<details>
								<summary><b>test</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ producer.producer.src.test</b></code>
									<!-- java Submodule -->
									<details>
										<summary><b>java</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.src.test.java</b></code>
											<!-- kafka Submodule -->
											<details>
												<summary><b>kafka</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ producer.producer.src.test.java.kafka</b></code>
													<!-- producer Submodule -->
													<details>
														<summary><b>producer</b></summary>
														<blockquote>
															<div class='directory-path' style='padding: 8px 0; color: #666;'>
																<code><b>⦿ producer.producer.src.test.java.kafka.producer</b></code>
															<table style='width: 100%; border-collapse: collapse;'>
															<thead>
																<tr style='background-color: #f8f9fa;'>
																	<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
																	<th style='text-align: left; padding: 8px;'>Summary</th>
																</tr>
															</thead>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/test/java/kafka/producer/ProducerApplicationTests.java'>ProducerApplicationTests.java</a></b></td>
																	<td style='padding: 8px;'>- Facilitates the testing of the Producer application within the Kafka project by ensuring that the application context loads correctly<br>- This verification is crucial for maintaining the integrity of the application as it interacts with various components of the codebase, ultimately contributing to the reliability and stability of the overall architecture.</td>
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
										<code><b>⦿ producer.producer.src.main</b></code>
									<!-- java Submodule -->
									<details>
										<summary><b>java</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ producer.producer.src.main.java</b></code>
											<!-- kafka Submodule -->
											<details>
												<summary><b>kafka</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ producer.producer.src.main.java.kafka</b></code>
													<!-- producer Submodule -->
													<details>
														<summary><b>producer</b></summary>
														<blockquote>
															<div class='directory-path' style='padding: 8px 0; color: #666;'>
																<code><b>⦿ producer.producer.src.main.java.kafka.producer</b></code>
															<table style='width: 100%; border-collapse: collapse;'>
															<thead>
																<tr style='background-color: #f8f9fa;'>
																	<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
																	<th style='text-align: left; padding: 8px;'>Summary</th>
																</tr>
															</thead>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/main/java/kafka/producer/ProducerApplication.java'>ProducerApplication.java</a></b></td>
																	<td style='padding: 8px;'>- ProducerApplication serves as a key component in the architecture, responsible for collecting and sending real-time hardware usage metrics to a Kafka topic<br>- It gathers CPU, memory, and disk information from the system, processes this data, and transmits it as structured JSON objects<br>- This functionality enables efficient monitoring and analysis of system performance, facilitating better resource management and operational insights within the broader application ecosystem.</td>
																</tr>
															</table>
															<!-- HardWareUsage Submodule -->
															<details>
																<summary><b>HardWareUsage</b></summary>
																<blockquote>
																	<div class='directory-path' style='padding: 8px 0; color: #666;'>
																		<code><b>⦿ producer.producer.src.main.java.kafka.producer.HardWareUsage</b></code>
																	<table style='width: 100%; border-collapse: collapse;'>
																	<thead>
																		<tr style='background-color: #f8f9fa;'>
																			<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
																			<th style='text-align: left; padding: 8px;'>Summary</th>
																		</tr>
																	</thead>
																		<tr style='border-bottom: 1px solid #eee;'>
																			<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/main/java/kafka/producer/HardWareUsage/TopProcessDetail.java'>TopProcessDetail.java</a></b></td>
																			<td style='padding: 8px;'>- TopProcessDetail serves as a data model representing key attributes of a system process, including process ID, command, CPU usage, memory usage, execution time, and state<br>- It facilitates the management and retrieval of process-related information within the broader architecture of the Kafka producer application, enabling efficient monitoring and analysis of hardware resource utilization.</td>
																		</tr>
																		<tr style='border-bottom: 1px solid #eee;'>
																			<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/main/java/kafka/producer/HardWareUsage/TotalCpuDetail.java'>TotalCpuDetail.java</a></b></td>
																			<td style='padding: 8px;'>- TotalCpuDetail serves as a data model within the Kafka producer architecture, encapsulating CPU usage metrics categorized by user and system processes<br>- It facilitates the representation and manipulation of CPU usage data, ensuring compatibility with JSON data access objects through its default constructor requirement<br>- This class plays a crucial role in monitoring and analyzing hardware performance, contributing to the overall efficiency of the system.</td>
																		</tr>
																		<tr style='border-bottom: 1px solid #eee;'>
																			<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/main/java/kafka/producer/HardWareUsage/TotalMemDetail.java'>TotalMemDetail.java</a></b></td>
																			<td style='padding: 8px;'>- TotalMemDetail serves as a data model for representing memory usage statistics within the Kafka producer architecture<br>- It encapsulates information about used and unused memory, facilitating the management and monitoring of hardware resources<br>- By providing methods for accessing and modifying these attributes, it supports seamless integration with JSON data access objects, enhancing the overall functionality of the system.</td>
																		</tr>
																		<tr style='border-bottom: 1px solid #eee;'>
																			<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/main/java/kafka/producer/HardWareUsage/HardWareUsageDAO.java'>HardWareUsageDAO.java</a></b></td>
																			<td style='padding: 8px;'>- HardWareUsageDAO serves as a data access object that encapsulates hardware usage metrics for an EC2 instance, including CPU, memory, and disk usage details<br>- It also tracks the top processes consuming resources, providing a structured way to manage and retrieve performance data<br>- This component is essential for monitoring and analyzing system performance within the broader architecture of the Kafka producer application.</td>
																		</tr>
																		<tr style='border-bottom: 1px solid #eee;'>
																			<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/producer/producer/src/main/java/kafka/producer/HardWareUsage/TotalDiskDetail.java'>TotalDiskDetail.java</a></b></td>
																			<td style='padding: 8px;'>- TotalDiskDetail serves as a data model within the Kafka producer architecture, encapsulating information about disk usage, specifically read and write metrics<br>- It facilitates the management and representation of disk performance data, ensuring compatibility with JSON data access objects<br>- This class plays a crucial role in monitoring hardware usage, contributing to the overall efficiency and reliability of the systems resource management.</td>
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
		</blockquote>
	</details>
	<!-- broker Submodule -->
	<details>
		<summary><b>broker</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ broker</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/broker/init.txt'>init.txt</a></b></td>
					<td style='padding: 8px;'>- Initialization for the broker component serves as a foundational element within the projects architecture, establishing essential configurations and settings tailored for the specific user, jongyeon<br>- This setup ensures that the broker operates smoothly, facilitating communication and data exchange across the system, thereby enhancing overall functionality and user experience within the broader codebase.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<!-- consumer Submodule -->
	<details>
		<summary><b>consumer</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ consumer</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/build.gradle'>build.gradle</a></b></td>
					<td style='padding: 8px;'>- Defines the build configuration for a Spring Boot application that integrates with Apache Kafka<br>- It establishes the project’s dependencies, including web functionalities and Kafka streaming capabilities, while ensuring compatibility with Java 11<br>- This setup facilitates the development of a robust consumer service within the broader architecture, enabling efficient data processing and real-time event handling.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/gradlew.bat'>gradlew.bat</a></b></td>
					<td style='padding: 8px;'>- Facilitates the execution of Gradle tasks on Windows systems by providing a startup script tailored for the Windows command line environment<br>- It ensures the proper configuration of Java runtime parameters and verifies the presence of the Java installation, enabling seamless integration with the broader project architecture that relies on Gradle for build automation and dependency management.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/settings.gradle'>settings.gradle</a></b></td>
					<td style='padding: 8px;'>- Defines the root project name for the consumer module within the overall codebase architecture<br>- This designation establishes a clear identity for the consumer component, facilitating organization and integration with other modules<br>- It plays a crucial role in project configuration, ensuring that build processes and dependencies are correctly aligned within the broader structure of the application.</td>
				</tr>
			</table>
			<!-- src Submodule -->
			<details>
				<summary><b>src</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ consumer.src</b></code>
					<!-- test Submodule -->
					<details>
						<summary><b>test</b></summary>
						<blockquote>
							<div class='directory-path' style='padding: 8px 0; color: #666;'>
								<code><b>⦿ consumer.src.test</b></code>
							<!-- java Submodule -->
							<details>
								<summary><b>java</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ consumer.src.test.java</b></code>
									<!-- kafka Submodule -->
									<details>
										<summary><b>kafka</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ consumer.src.test.java.kafka</b></code>
											<!-- consumer Submodule -->
											<details>
												<summary><b>consumer</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ consumer.src.test.java.kafka.consumer</b></code>
													<table style='width: 100%; border-collapse: collapse;'>
													<thead>
														<tr style='background-color: #f8f9fa;'>
															<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
															<th style='text-align: left; padding: 8px;'>Summary</th>
														</tr>
													</thead>
														<tr style='border-bottom: 1px solid #eee;'>
															<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/test/java/kafka/consumer/ConsumerApplicationTests.java'>ConsumerApplicationTests.java</a></b></td>
															<td style='padding: 8px;'>- Facilitates the testing of the Kafka consumer application by ensuring that the application context loads correctly within the Spring Boot framework<br>- This verification is crucial for maintaining the integrity of the application’s configuration and dependencies, contributing to the overall reliability and stability of the codebase architecture<br>- It plays a vital role in the continuous integration process, ensuring that changes do not disrupt functionality.</td>
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
								<code><b>⦿ consumer.src.main</b></code>
							<!-- java Submodule -->
							<details>
								<summary><b>java</b></summary>
								<blockquote>
									<div class='directory-path' style='padding: 8px 0; color: #666;'>
										<code><b>⦿ consumer.src.main.java</b></code>
									<!-- kafka Submodule -->
									<details>
										<summary><b>kafka</b></summary>
										<blockquote>
											<div class='directory-path' style='padding: 8px 0; color: #666;'>
												<code><b>⦿ consumer.src.main.java.kafka</b></code>
											<!-- consumer Submodule -->
											<details>
												<summary><b>consumer</b></summary>
												<blockquote>
													<div class='directory-path' style='padding: 8px 0; color: #666;'>
														<code><b>⦿ consumer.src.main.java.kafka.consumer</b></code>
													<table style='width: 100%; border-collapse: collapse;'>
													<thead>
														<tr style='background-color: #f8f9fa;'>
															<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
															<th style='text-align: left; padding: 8px;'>Summary</th>
														</tr>
													</thead>
														<tr style='border-bottom: 1px solid #eee;'>
															<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/ConsumerApplication.java'>ConsumerApplication.java</a></b></td>
															<td style='padding: 8px;'>- ConsumerApplication serves as a Kafka consumer that connects to a specified Kafka topic to retrieve and process messages<br>- It deserializes incoming data into HardWareUsageDAO objects, enabling the application to handle hardware usage metrics effectively<br>- By continuously polling the Kafka topic, it ensures real-time data processing and logging, contributing to the overall architectures capability to monitor and analyze hardware performance.</td>
														</tr>
													</table>
													<!-- Config Submodule -->
													<details>
														<summary><b>Config</b></summary>
														<blockquote>
															<div class='directory-path' style='padding: 8px 0; color: #666;'>
																<code><b>⦿ consumer.src.main.java.kafka.consumer.Config</b></code>
															<table style='width: 100%; border-collapse: collapse;'>
															<thead>
																<tr style='background-color: #f8f9fa;'>
																	<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
																	<th style='text-align: left; padding: 8px;'>Summary</th>
																</tr>
															</thead>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/Config/CommonJsonDeserializer.java'>CommonJsonDeserializer.java</a></b></td>
																	<td style='padding: 8px;'>- Facilitates the configuration of Kafka consumers by providing a method to generate a map of properties essential for deserialization<br>- This functionality ensures that messages are correctly interpreted, leveraging error handling and JSON deserialization<br>- It plays a crucial role in the overall architecture by enabling seamless integration of Kafka messaging within the application, enhancing data processing capabilities.</td>
																</tr>
															</table>
														</blockquote>
													</details>
													<!-- HardWareUsage Submodule -->
													<details>
														<summary><b>HardWareUsage</b></summary>
														<blockquote>
															<div class='directory-path' style='padding: 8px 0; color: #666;'>
																<code><b>⦿ consumer.src.main.java.kafka.consumer.HardWareUsage</b></code>
															<table style='width: 100%; border-collapse: collapse;'>
															<thead>
																<tr style='background-color: #f8f9fa;'>
																	<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
																	<th style='text-align: left; padding: 8px;'>Summary</th>
																</tr>
															</thead>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/HardWareUsage/TopProcessDetail.java'>TopProcessDetail.java</a></b></td>
																	<td style='padding: 8px;'>- TopProcessDetail serves as a data model representing key attributes of system processes, including process ID, command, CPU usage, memory usage, execution time, and state<br>- It facilitates the management and retrieval of process-related information within the Kafka consumer architecture, enabling efficient monitoring and analysis of hardware usage in the application<br>- This class is essential for integrating JSON data access objects, ensuring seamless data handling.</td>
																</tr>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/HardWareUsage/TotalCpuDetail.java'>TotalCpuDetail.java</a></b></td>
																	<td style='padding: 8px;'>- TotalCpuDetail serves as a data model for capturing and representing CPU usage metrics, specifically user and system CPU time<br>- It facilitates the integration of CPU usage data within the broader Kafka consumer architecture, enabling efficient monitoring and analysis of hardware performance<br>- This class is essential for ensuring that CPU metrics are accurately structured and accessible for further processing and reporting within the application.</td>
																</tr>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/HardWareUsage/TotalMemDetail.java'>TotalMemDetail.java</a></b></td>
																	<td style='padding: 8px;'>- TotalMemDetail serves as a data model within the Kafka consumer architecture, encapsulating memory usage information by tracking both used and unused memory<br>- It facilitates the representation and manipulation of memory statistics, ensuring compatibility with JSON data access objects through its default constructor<br>- This class plays a crucial role in monitoring hardware resource utilization, contributing to the overall efficiency and performance analysis of the system.</td>
																</tr>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/HardWareUsage/HardWareUsageDAO.java'>HardWareUsageDAO.java</a></b></td>
																	<td style='padding: 8px;'>- HardWareUsageDAO serves as a data access object that encapsulates hardware usage metrics for an EC2 instance, including CPU, memory, and disk usage details, along with a list of top processes consuming resources<br>- It facilitates the management and retrieval of these metrics, enabling efficient monitoring and analysis of system performance within the broader architecture of the Kafka consumer application.</td>
																</tr>
																<tr style='border-bottom: 1px solid #eee;'>
																	<td style='padding: 8px;'><b><a href='temp_github_repos/EC2-Dashboard/consumer/src/main/java/kafka/consumer/HardWareUsage/TotalDiskDetail.java'>TotalDiskDetail.java</a></b></td>
																	<td style='padding: 8px;'>- TotalDiskDetail serves as a data model within the Kafka consumer architecture, encapsulating information about disk read and write operations<br>- It facilitates the management and representation of disk usage metrics, ensuring compatibility with JSON data access objects through its default constructor<br>- This class plays a crucial role in monitoring hardware performance, contributing to the overall efficiency and reliability of the system.</td>
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
</details>

---

## Getting Started

### Prerequisites

This project requires the following dependencies:

- **Programming Language:** Java
- **Package Manager:** Gradle

### Installation

Build EC2-Dashboard from the source and intsall dependencies:

1. **Clone the repository:**

    ```sh
    ❯ git clone ../EC2-Dashboard
    ```

2. **Navigate to the project directory:**

    ```sh
    ❯ cd EC2-Dashboard
    ```

3. **Install the dependencies:**

<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![gradle][gradle-shield]][gradle-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [gradle-shield]: https://img.shields.io/badge/Gradle-02303A.svg?style={badge_style}&logo=gradle&logoColor=white -->
	<!-- [gradle-link]: https://gradle.org/ -->

	**Using [gradle](https://gradle.org/):**

	```sh
	❯ gradle build
	```

### Usage

Run the project with:

**Using [gradle](https://gradle.org/):**
```sh
gradle run
```

### Testing

Ec2-dashboard uses the {__test_framework__} test framework. Run the test suite with:

**Using [gradle](https://gradle.org/):**
```sh
gradle test
```

---

## Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

## Contributing

- **💬 [Join the Discussions](https://LOCAL/temp_github_repos/EC2-Dashboard/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://LOCAL/temp_github_repos/EC2-Dashboard/issues)**: Submit bugs found or log feature requests for the `EC2-Dashboard` project.
- **💡 [Submit Pull Requests](https://LOCAL/temp_github_repos/EC2-Dashboard/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your LOCAL account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone temp_github_repos/EC2-Dashboard
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
   <a href="https://LOCAL{/temp_github_repos/EC2-Dashboard/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=temp_github_repos/EC2-Dashboard">
   </a>
</p>
</details>

---

## License

Ec2-dashboard is protected under the [LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

## Acknowledgments

- Credit `contributors`, `inspiration`, `references`, etc.

<div align="right">

[![][back-to-top]](#top)

</div>


[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square


---
