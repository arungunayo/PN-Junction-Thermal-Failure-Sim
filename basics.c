#include <stdio.h>

int swith(int n){
    if(n == 0){
        return 1;
    }
    return 0;
}

int main(){
    int n = 0;
    for(int i = 0; i < 5; i ++){
        
        for (int j = 0; j < i+1; j++){
            n = swith(n) ;
            printf("%d",n);
            // n = swith(n);
        }
        printf("\n");
        n = swith(n) ;
    }
}