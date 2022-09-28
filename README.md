# git-tracker

A simple REST API allowing users to create collections of Git repositories. Each repository in collection includes information about e.g. date of last commit and release. Currently, GitHub and GitLab repositories are supported.

## Running and testing

#### Ensure that Docker and Docker Compose are installed

#### Clone the project
    git clone https://github.com/lukaszsmolinski/git-tracker.git
    
#### Go to project's root directory
    cd git-tracker
  
#### Provide configuration
Create `.env` and `.env.test` files and set required options (such as database connection details). 
Full list of available options can be found in `config.py`. 

It is recommended to provide GitHub API authentication details, since unathenticated requests have low rate limit.

#### Run
    docker compose up -d --build
  
#### Test
    docker compose exec web pytest
    
## Endpoints
Swagger documentation is available (while the app is running) at `<app url>/docs`.
