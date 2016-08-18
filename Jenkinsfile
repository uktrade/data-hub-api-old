node {
   stage 'Checkout'
   checkout scm

   stage 'Unit test'
   wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm']) {
     sh 'docker-compose -p datahubapi-${BRANCH_NAME} up --build --force-recreate --remove-orphans -d'
   }
   wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm']) {
     sh 'docker-compose -p datahubapi-${BRANCH_NAME} run --rm app make lint test'
   }
   wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm']) {
     sh 'docker-compose -p datahubapi-${BRANCH_NAME} down --rmi all -v --remove-orphans'
   }

   stage 'Capture test results'
   // TODO: Create test reports
   // step([$class: 'JUnitResultArchiver', testResults: 'results/**/*.xml'])

   stage 'Clean workspace'
   deleteDir()
}
