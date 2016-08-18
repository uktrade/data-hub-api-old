node {
   stage 'Checkout'
   checkout scm

   stage 'Unit test'
   sh 'docker-compose up'
   sh 'docker-compose down'

   stage 'Capture test results'
   step([$class: 'JUnitResultArchiver', testResults: 'results/**/*.xml'])

   stage 'Clean workspace'
   deleteDir()
}
