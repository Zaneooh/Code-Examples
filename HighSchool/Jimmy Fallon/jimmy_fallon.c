#include <stdlib.h> 
#include <stdio.h>
#include <unistd.h>  
#include <pthread.h>
#include <semaphore.h>
sem_t operators;
sem_t connected_lock;
//pthread_t next_id;
int next_id;

void* phonecall(void* vargp) {   
  static int NUM_OPERATORS = 3;
  static int NUM_LINES = 5;
  static int connected = 0;// Callers that are connected  
  int id=next_id++;

  sem_wait(&connected_lock);
    if(connected>=NUM_LINES){
      printf("%i is calling line, busy signal\n",id);
      while(connected>=NUM_LINES){ //waits for line to open
        sem_post(&connected_lock);
      }
    }
    connected++;    
  sem_post(&connected_lock);

  printf("%i has available line, call ringing\n",id);
  
  sem_wait(&operators);//waits for operator to be free
  printf("Caller number %i is ordering\n",id); 
  sleep(1);
  printf("Order %i is complete\n",id);
  //Proceed with ticket ordering process  
  sem_post(&operators);

  sem_wait(&connected_lock);
  connected--;//disconnects caller from the line
  sem_post(&connected_lock);

  printf("Order %i hungup\n",id);
  return vargp;
}

int main() {
  next_id=0;  
  sem_init(&connected_lock, 0, 1);
  sem_init(&operators, 0, 3);
  pthread_t threads[240];
  for(int i=0;i<240;i++){
    pthread_create(&threads[i], NULL, phonecall, NULL);//creates phonecalls
  }
  for(int i=0;i<240;i++){
    pthread_join(threads[i],NULL);//waits for end of calls
  }
}

