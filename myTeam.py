# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

from captureAgents import CaptureAgent
import random, time, util
from game import Directions, Actions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DefensiveReflexAgent', second = 'OffensiveReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ExpectimaxAgent(CaptureAgent):

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).
    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)
    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    self.distancer.getMazeDistances()

    # Start position of our agent.
    self.start = gameState.getInitialAgentPosition(self.index)

    # Center of the board.
    self.midWidth = gameState.data.layout.width/2
    self.midHeight = gameState.data.layout.height/2
    self.legalPositions = [p for p in gameState.getWalls().asList(False) if p[1] > 1]
    self.team = self.getTeam(gameState)
    self.enemies = self.getOpponents(gameState)

  def chooseAction(self, gameState):
        
    myPos = gameState.getAgentPosition(self.index)      
    newState = gameState.deepCopy()
    
    for enemy in self.enemies:
        enemyPosition =  gameState.getAgentPosition(enemy)
        conf = game.Configuration(enemyPosition, Directions.STOP)
        newState.data.agentStates[enemy] = game.AgentState(conf, newState.isRed(enemyPosition) != newState.isOnRedTeam(enemy))

    action = self.maxFunction(newState, depth=2)[1]
    return action

  
  def maxFunction(self, gameState, depth):   
      if  depth == 0 or gameState.isOver():
          return self.evaluationScore(gameState), Directions.STOP    

      actions = gameState.getLegalActions(self.index)   
      successorGameStates = [gameState.generateSuccessor(self.index, action)
                                for action in actions]
  
      scores = [self.expectiFunction(successorGameState, self.enemies[0], depth)[0]
                  for successorGameState in successorGameStates]
      bestScore = max(scores)
      bestIndices = [index for index in range(len(scores)) if
                        scores[index] == bestScore]
      chosenIndex = random.choice(bestIndices)
      return bestScore, actions[chosenIndex]

  def expectiFunction(self, gameState, enemy, depth):                 
    if gameState.isOver() or depth == 0:
        return self.evaluationScore(gameState), Directions.STOP
    
    actions = gameState.getLegalActions(enemy)   
    successorGameStates = []
    for action in actions:
      try:
          successorGameStates.append(gameState.generateSuccessor(enemy, action))
      except:
          pass
 
    if enemy < max(self.enemies):
        scores = [self.expectiFunction(successorGameState, enemy + 2, depth)[0]
                    for successorGameState in successorGameStates]
    else:
        scores = [self.maxFunction(successorGameState, depth - 1)[0]
                    for successorGameState in successorGameStates]

    # Here we can improve the probability inference of each actions. Which is more likely to happen. We didnt (No time D:)
    expectedScore = sum(scores) / len(scores)  
    return expectedScore, Directions.STOP

  def enemyDistances(self, gameState):    
    dists = []
    for enemy in self.enemies:
        myPos = gameState.getAgentPosition(self.index)
        enemyPos = gameState.getAgentPosition(enemy)      
        dists.append((enemy, self.distancer.getDistance(myPos, enemyPos)))
    return dists

class OffensiveAgent(ExpectimaxAgent):
  def registerInitialState(self, gameState):
      ExpectimaxAgent.registerInitialState(self, gameState)
      self.retreating = False

  def chooseAction(self, gameState):  
      scaredTimes = [gameState.getAgentState(enemy).scaredTimer for enemy in self.enemies]      
      score = self.getScore(gameState)
      
      # Could be Updated to be different from our team and the enemies.
      if score < 7:
        carryLimit = 6
      else:
        carryLimit = 4

      if gameState.getAgentState(self.index).numCarrying < carryLimit and len(self.getFood(gameState).asList()) > 2:
        self.retreating = False
      else:
        if min(scaredTimes) > 5: # Do not retreat but search for food.
            self.retreating = False
        else:
            self.retreating = True
      return ExpectimaxAgent.chooseAction(self, gameState)


  def evaluationScore(self, gameState):
    myPos = gameState.getAgentPosition(self.index)    
    targetFood = self.getFood(gameState).asList()
    
    ghostDistances = []
    for enemy in self.enemies:
      if not gameState.getAgentState(enemy).isPacman:
          enemyPos = gameState.getAgentPosition(enemy)
          if enemyPos != None:
              ghostDistances.append(self.distancer.getDistance(myPos, enemyPos))
    
    minGhostDistances = min(ghostDistances) if len(ghostDistances) else 0

    if self.retreating:     
      distanceFromStart = min([self.distancer.getDistance(myPos, (self.midWidth, i))
                      for i in range(gameState.data.layout.height)
                      if (self.midWidth, i) in self.legalPositions])
      return  500 * minGhostDistances - 2 * distanceFromStart
    else:    

      # Power pill hunt
      capsulesChasing = None
      if self.red:
          capsulesChasing = gameState.getBlueCapsules()
      else:
          capsulesChasing = gameState.getRedCapsules()
      
      capsulesChasingDistances = [self.distancer.getDistance(myPos, capsule) for capsule in
                                  capsulesChasing]
      minCapsuleChasingDistance = min(capsulesChasingDistances) if len(capsulesChasingDistances) else 0 
      foodDistances = [self.distancer.getDistance(myPos, food) for
                             food in targetFood]
      minFoodDistance = min(foodDistances) if len(foodDistances) else 0
      scaredTimes = [gameState.getAgentState(enemy).scaredTimer for enemy
                        in self.enemies]

      # We are scared
      if minGhostDistances < 4 and min(scaredTimes) >= 3:
        minGhostDistances *= -1    
      return 2 * self.getScore(gameState) - 50 * len(targetFood) - \
              3 * minFoodDistance - 10000 * len(capsulesChasing) - \
              5 * minCapsuleChasingDistance + 200 * minGhostDistances


class DefensiveAgent(ExpectimaxAgent):
    def registerInitialState(self, gameState):
        ExpectimaxAgent.registerInitialState(self, gameState)
        self.offensing = False

    def chooseAction(self, gameState):
        # Is there a pacman?
        enemiesWithin = [a for a in self.enemies if
                    gameState.getAgentState(a).isPacman]
        numWithin = len(enemiesWithin)

        # Enemy activated power pill?
        scaredTimes = [gameState.getAgentState(enemy).scaredTimer for enemy in
                         self.enemies]
            
        if numWithin == 0 or min(scaredTimes) > 8:
            self.offensing = True
        else:
            self.offensing = False
        return ExpectimaxAgent.chooseAction(self, gameState)

    def evaluationScore(self, gameState):
        myPos = gameState.getAgentPosition(self.index)        
        enemyDistances = self.enemyDistances(gameState)

        if(self.offensing == False):
          # If the enemy is on our side
          invaders = [a for a in self.enemies if
                      gameState.getAgentState(a).isPacman]
          
          pac_distances = [dist for id, dist in enemyDistances if
                            gameState.getAgentState(id).isPacman]
          minPacDistances = min(pac_distances) if len(pac_distances) else 0

          capsules = self.getCapsulesYouAreDefending(gameState)
          capsulesDistances = [self.getMazeDistance(myPos, capsule) for capsule in
                                capsules]
          minCapsuleDistance = min(capsulesDistances) if len(capsulesDistances) else 0
          return - 10 * minPacDistances - minCapsuleDistance - 999999 * len(invaders)
        else:                 
          targetFood = self.getFood(gameState).asList()
          foodDistances = [self.distancer.getDistance(myPos, food) for food in
                          targetFood]
          minFoodDistance = min(foodDistances) if len(foodDistances) else 0    
          return 2 * self.getScore(gameState) - 100 * len(targetFood) - \
                  300 * minFoodDistance

class defenseAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  indicatorOfFood = 0
  foodToDefend = 0

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
    
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v >= maxValue]
    
    # Obtenemos el estado sucesor de realizar una accion elegida aleatoriamente
    
    successor = self.getSuccessor(gameState, random.choice(actions))
    
    # Obtenemos la lista de enemigos
    
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    
    # Obtenemos la lista de enemigos que son Pacman
    
    pacmanEnemies = [a for a in enemies if a.isPacman and a.getPosition() != None]
        
    # Obtenemos la lista de comida que debemos defender
    
    foodDefending = self.getFoodYouAreDefending(gameState).asList()
    
    # Elegimos una comida aleatoria para defender
    
    if self.indicatorOfFood == 0:
        
        self.foodToDefend = random.choice(foodDefending)
        self.indicatorOfFood = self.indicatorOfFood + 1
    
    # Obtenemos acciones optimas que nos lleven a la comida elegida mientras no se detecte un Pacman
    
    if len(pacmanEnemies) == 0:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.foodToDefend,pos2)
        
        if dist < bestDist:
          bestAction = action
          bestDist = dist
            
        if dist == 0:
            self.foodToDefend = random.choice(foodDefending)
       
      return bestAction
    
    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """

    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class attackAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
    
  maxFood = 20  
  randomAction = 0
  eatCapsule = 30
    
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    
    # Se obtiene las acciones que se pueden realizar
    
    actions = gameState.getLegalActions(self.index)
    
    # Obtiene los valores de aplicar una accion en el estado actual
    
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
    
    if self.randomAction == 0:
        
        maxValue = max(values)
        
        # Obtiene las acciones que tienen un valor igual a maxValue
    
        bestActions = [a for a, v in zip(actions, values) if v >= maxValue]
    
    if self.randomAction != 0:
        
        minValue = min(values)
        self.randomAction = self.randomAction - 1
        
        # Obtiene las acciones que lo alejan lo suficiente del fantasma para que se vaya
        
        bestActions = [a for a, v in zip(actions, values) if v <= minValue]

    # Obtiene lista de capsulas de poder
    
    powerCapsules = self.getCapsules(gameState)
    
    # Obtiene la cantidad de comida que falta del equipo enemigo
    
    foodLeft = len(self.getFood(gameState).asList())
    scorePacman = self.maxFood - foodLeft
    
    chosenAction = random.choice(bestActions) # Elige una accion aleatoriamente
    
    # Obtiene la distancia a los enemigos si es que son fantasmas
    
    successor = self.getSuccessor(gameState, chosenAction) # Estado del juego si se realiza la accion elegida aleatoriamente
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)] # Estado de enemigos en el estado sucesor
    ghostEnemies = [a for a in enemies if not a.isPacman and a.getPosition() != None] # Guarda enemigos si son fantasmas
    
    myPos = successor.getAgentPosition(self.index)
    
    distsGhosts = [self.getMazeDistance(myPos, a.getPosition()) for a in ghostEnemies] # Distancia hacia enemigos
    
    # Si detecta que ya no hay capsulas de poder, se mueve por donde quiera por cierto tiempo
    
    if len(powerCapsules) == 0:
        
        if self.eatCapsule != 0:
            
            self.eatCapsule = self.eatCapsule - 1
            
            return chosenAction
    
    # Vuelve a casa cuando el enemigo esta demasiado cerca
    
    if len(distsGhosts) != 0:
        
        if min(distsGhosts) <= 5:
          bestDist = 9999
          self.randomAction = 5
            
          # Obtiene acciones que lo hacen escapar del fantasma  
          
          for enemies in ghostEnemies:
              escapeActions = [action for action in actions if self.getMazeDistance(self.getSuccessor(gameState, action).
                                                                                    getAgentPosition(self.index), 
                                                                                    enemies.getPosition()) > 2]
          
          if len(escapeActions) != 0:
           
              for action in escapeActions:
            
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start,pos2)

                if dist < bestDist:
                
                    bestAction = action
                    bestDist = dist
              
              return bestAction
            
          if len(escapeActions) == 0:
                
              for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start,pos2)

                if dist < bestDist:
                  bestAction = action
                  bestDist = dist
            
              return bestAction

    # Vuelve a casa si la comida faltante es menor o igual 2
    
    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist    
      return bestAction
    
    # Elige una accion aleatoriamente, ya que tienen el mismo valor    
    return chosenAction

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
        
    # Estado del juego si es que se realiza la accion (objeto GameState)
    
    successor = gameState.generateSuccessor(self.index, action)
    
    # Obtiene la posicion del agente
    
    pos = successor.getAgentState(self.index).getPosition()
    
    # Verifica si la posicion del agente es la misma que el punto cercano 
    
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    
    # Obtiene el valor que tiene realizar una accion
    
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveReflexAgent(attackAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()    
    features['successorScore'] = -len(foodList) #self.getScore(successor)
    
    # Compute distance to the nearest food

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1}

class DefensiveReflexAgent(defenseAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    
    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    
    # Obtiene el estado de los enemigos cuando realice la accion
    
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    
    # Guarda los invasores que puede observar si es que son Pacman
    
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    
    # Guarda la cantidad de invasores
    
    features['numInvaders'] = len(invaders)
    
    # Si encuentra invasores calcula la distancia hacia ellos
    
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
        
    # Si la accion es detenerse, actualiza la caracteristica 'stop' a 1

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}