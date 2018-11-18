# devops-callenge
## Installation

    python -m virtualenv ~/Projects/skaarj/virtualenv
    source ~/Projects/skaarj/virtualenv/bin/activate
    pip install -r requirements.txt
    docker pull amazon/dynamodb-local


## List all images

    Protocol: GET
    URI: /api/v1/images
    Request body: EMPTY

## Request a single image

    Protocol: GET
    URI: /api/v1/images/name/test1
    Request body: EMPTY

## Request book creation

    Protocol: POST
    URI: /api/v1/images
    Request body:

    {
        name: 'Docker logo',
        url: 'https://www.docker.com/sites/default/files/Whale%20Logo332_5.png'
    }
