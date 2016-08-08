var myApp = angular.module('myApp', [])
    .config(function($interpolateProvider) {
        $interpolateProvider.startSymbol('[[').endSymbol(']]');
    });

myApp.controller('RelaysController', function($scope, $http, $interval){
  $scope.header = 'Relay status';

  var getRelaysInfo = function() {
    $http.get("/api/v1.0/relays").then(function(response){
      var relays = response.data.relays;
      $scope.relays = relays;
      }, function(error){}
    );
  };

  $scope.toggleRelay = function(relay) {
    var newState = 'off';
    if (relay.state == 'off') {
      newState = 'on'
    }
    $scope.newState = newState;

    $http.put("/api/v1.0/relays/"+relay.id, {state : newState}).then(function(response){
      relay = response.data.relay;
      for (var i=0; i < $scope.relays.length; i++) {
        if ($scope.relays[i].id == relay.id) {
          $scope.relays[i] = relay;
          break;
        }
      }
    }, function(error) {}
    );
  }
  $interval(function(){
    getRelaysInfo();
  }, 500)
  
});