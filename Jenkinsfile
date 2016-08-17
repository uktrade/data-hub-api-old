// see https://dzone.com/refcardz/continuous-delivery-with-jenkins-workflow for tutorial
// see https://documentation.cloudbees.com/docs/cookbook/_pipeline_dsl_keywords.html for DSL reference
node {
   // Mark the code checkout 'stage'....

   stage 'Prepare test'
   sh 'mkdir reports'

   stage 'Unit test'
   sh 'docker-compose -p data-hub-api-${BRANCH_NAME} up -d db'
   sh 'docker-compose -p data-hub-api-${BRANCH_NAME} up django'
   sh 'docker-compose -p data-hub-api-${BRANCH_NAME} stop'

   stage 'Capture test results'
   step([$class: 'JUnitResultArchiver', testResults: 'results/**/*.xml'])

   stage 'Clean workspace'
   deleteDir()
}
