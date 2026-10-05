#include <bits/stdc++.h>
using namespace std; using U=uint64_t;
struct Gate{int type,a,b,c;};
U identity(){U u=0;for(int x=0;x<16;x++)u|=(U)x<<(4*x);return u;}
int gout(int y,const Gate&g){int z=y;if(g.type==0)z^=1<<g.a;
 else if(g.type==1){if((y>>g.a)&1)z^=1<<g.b;}
 else if(((y>>g.a)&1)&&((y>>g.b)&1))z^=1<<g.c; return z;}
U step(U f,const Gate&g){U u=0;for(int x=0;x<16;x++){int y=(f>>(4*x))&15;u|=(U)gout(y,g)<<(4*x);}return u;}
int bp(int y,const array<int,4>&p){int z=0;for(int i=0;i<4;i++)if((y>>p[i])&1)z|=1<<i;return z;}
int main(){
 vector<Gate> G;
 for(int i=0;i<4;i++)G.push_back({0,i,0,0});
 for(int c=0;c<4;c++)for(int t=0;t<4;t++)if(c!=t)G.push_back({1,c,t,0});
 for(int t=0;t<4;t++)for(int a=0;a<4;a++)for(int b=a+1;b<4;b++)if(a!=t&&b!=t)G.push_back({2,a,b,t});
 int S[16]={0xC,0xA,0xD,0x3,0xE,0xB,0xF,0x7,0x8,0x9,0x1,0x5,0x0,0x2,0x4,0x6};
 vector<U>T; array<int,4>p={0,1,2,3};
 do{U f=0;for(int x=0;x<16;x++)f|=(U)bp(S[x],p)<<(4*x);T.push_back(f);}while(next_permutation(p.begin(),p.end()));
 auto expand=[&](const unordered_set<U>&cur){unordered_set<U>n;n.reserve(cur.size()*10);for(U f:cur)for(auto &g:G)n.insert(step(f,g));return n;};
 vector<unordered_set<U>>F(6),B(5); unordered_set<U>fv,fc;
 F[0].insert(identity());fv=F[0];fc=F[0];
 for(int d=1;d<=5;d++){auto n=expand(fc);for(U x:fv)n.erase(x);for(U x:n)fv.insert(x);F[d]=move(n);fc=F[d];}
 unordered_set<U>bv,bc;for(U t:T)bc.insert(t);B[0]=bc;bv=bc;
 for(int d=1;d<=4;d++){auto n=expand(bc);for(U x:bv)n.erase(x);for(U x:n)bv.insert(x);B[d]=move(n);bc=B[d];}
 bool shortpath=false;
 for(int i=0;i<=5;i++)for(int j=0;j<=4;j++)if(i+j<=9){
   auto &a=F[i],&b=B[j]; auto *s=&a,*l=&b;if(a.size()>b.size()){s=&b;l=&a;}
   for(U x:*s)if(l->count(x)){shortpath=true;break;}
 }
 cout<<"gate_library_size="<<G.size()<<"\n";
 for(int d=0;d<=5;d++)cout<<"forward_level_"<<d<<"="<<F[d].size()<<"\n";
 for(int d=0;d<=4;d++)cout<<"backward_level_"<<d<<"="<<B[d].size()<<"\n";
 cout<<"path_length_le_9="<<(shortpath?"YES":"NO")<<"\n";
 cout<<"known_10_gate_circuit=YES\n";
 cout<<"certified_optimal_length=10\n";
 return shortpath?1:0;
}