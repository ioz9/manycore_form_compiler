// Generated by the Manycore Form Compiler.
// https://github.com/gmarkall/manycore_form_compiler


#include "cudastatic.hpp"
#include "cudastate.hpp"
double* localVector;
double* localMatrix;
double* globalVector;
double* globalMatrix;
double* solutionVector;
int* Velocity_findrm;
int Velocity_findrm_size;
int* Velocity_colm;
int Velocity_colm_size;


__global__ void A(int n_ele, double* localTensor, double dt, double* c0)
{
  const double CG1_v[2][6][6] = { { {  0.0915762135097707,
                                     0.0915762135097707,
                                     0.8168475729804585,
                                     0.4459484909159649,
                                     0.4459484909159649,
                                     0.1081030181680702 },
                                   {  0.0915762135097707,
                                     0.8168475729804585,
                                     0.0915762135097707,
                                     0.4459484909159649,
                                     0.1081030181680702,
                                     0.4459484909159649 },
                                   {  0.8168475729804585,
                                     0.0915762135097707,
                                     0.0915762135097707,
                                     0.1081030181680702,
                                     0.4459484909159649,
                                     0.4459484909159649 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 } },

                                  { {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.0915762135097707,
                                     0.0915762135097707,
                                     0.8168475729804585,
                                     0.4459484909159649,
                                     0.4459484909159649,
                                     0.1081030181680702 },
                                   {  0.0915762135097707,
                                     0.8168475729804585,
                                     0.0915762135097707,
                                     0.4459484909159649,
                                     0.1081030181680702,
                                     0.4459484909159649 },
                                   {  0.8168475729804585,
                                     0.0915762135097707,
                                     0.0915762135097707,
                                     0.1081030181680702,
                                     0.4459484909159649,
                                     0.4459484909159649 } } };
  const double d_CG1[3][6][2] = { { {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. } },

                                  { {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. } },

                                  { { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. } } };
  const double w[6] = {  0.0549758718276609, 0.0549758718276609,
                         0.0549758718276609, 0.1116907948390057,
                         0.1116907948390057, 0.1116907948390057 };
  double c_q0[6][2][2];
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int q_r_0 = 0; q_r_0 < 3; q_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * q_r_0)] * d_CG1[q_r_0][i_g][i_d_1];
          };
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 6; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 6; i_r_1++)
      {
        localTensor[i_ele + n_ele * (i_r_0 + 6 * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          double ST1 = 0.0;
          double ST0 = 0.0;
          ST1 += c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0];
          for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
          {
            ST0 += CG1_v[i_d_0][i_r_0][i_g] * CG1_v[i_d_0][i_r_1][i_g];
          };
          localTensor[i_ele + n_ele * (i_r_0 + 6 * i_r_1)] += ST0 * ST1 * w[i_g];
        };
      };
    };
  };
}

__global__ void RHS(int n_ele, double* localTensor, double dt, double* c0, double* c1)
{
  const double CG1[3][6] = { {  0.0915762135097707, 0.0915762135097707,
                               0.8168475729804585, 0.4459484909159649,
                               0.4459484909159649, 0.1081030181680702 },
                             {  0.0915762135097707, 0.8168475729804585,
                               0.0915762135097707, 0.4459484909159649,
                               0.1081030181680702, 0.4459484909159649 },
                             {  0.8168475729804585, 0.0915762135097707,
                               0.0915762135097707, 0.1081030181680702,
                               0.4459484909159649, 0.4459484909159649 } };
  const double CG1_v[2][6][6] = { { {  0.0915762135097707,
                                     0.0915762135097707,
                                     0.8168475729804585,
                                     0.4459484909159649,
                                     0.4459484909159649,
                                     0.1081030181680702 },
                                   {  0.0915762135097707,
                                     0.8168475729804585,
                                     0.0915762135097707,
                                     0.4459484909159649,
                                     0.1081030181680702,
                                     0.4459484909159649 },
                                   {  0.8168475729804585,
                                     0.0915762135097707,
                                     0.0915762135097707,
                                     0.1081030181680702,
                                     0.4459484909159649,
                                     0.4459484909159649 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 } },

                                  { {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                ,
                                     0.                , 0.                 },
                                   {  0.0915762135097707,
                                     0.0915762135097707,
                                     0.8168475729804585,
                                     0.4459484909159649,
                                     0.4459484909159649,
                                     0.1081030181680702 },
                                   {  0.0915762135097707,
                                     0.8168475729804585,
                                     0.0915762135097707,
                                     0.4459484909159649,
                                     0.1081030181680702,
                                     0.4459484909159649 },
                                   {  0.8168475729804585,
                                     0.0915762135097707,
                                     0.0915762135097707,
                                     0.1081030181680702,
                                     0.4459484909159649,
                                     0.4459484909159649 } } };
  const double d_CG1[3][6][2] = { { {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. } },

                                  { {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. } },

                                  { { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. } } };
  const double w[6] = {  0.0549758718276609, 0.0549758718276609,
                         0.0549758718276609, 0.1116907948390057,
                         0.1116907948390057, 0.1116907948390057 };
  double c_q1[6][2];
  double c_q0[6][2][2];
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        c_q1[i_g][i_d_0] = 0.0;
        for(int q_r_0 = 0; q_r_0 < 3; q_r_0++)
        {
          c_q1[i_g][i_d_0] += c1[i_ele + n_ele * (i_d_0 + 2 * q_r_0)] * CG1[q_r_0][i_g];
        };
      };
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int q_r_0 = 0; q_r_0 < 3; q_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * q_r_0)] * d_CG1[q_r_0][i_g][i_d_1];
          };
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 6; i_r_0++)
    {
      localTensor[i_ele + n_ele * i_r_0] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        double ST3 = 0.0;
        double ST2 = 0.0;
        ST3 += c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0];
        for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
        {
          ST2 += CG1_v[i_d_0][i_r_0][i_g] * c_q1[i_g][i_d_0];
        };
        localTensor[i_ele + n_ele * i_r_0] += ST2 * ST3 * w[i_g];
      };
    };
  };
}

StateHolder* state;
extern "C" void initialise_gpu_()
{
  state = new StateHolder();
  state->initialise();
  state->extractField("Coordinate", 1);
  state->extractField("Velocity", 1);
  state->allocateAllGPUMemory();
  state->transferAllFields();
  int numEle = state->getNumEle();
  int numNodes = state->getNumNodes();
  CsrSparsity* Velocity_sparsity = state->getSparsity("Velocity");
  Velocity_colm = Velocity_sparsity->getCudaColm();
  Velocity_findrm = Velocity_sparsity->getCudaFindrm();
  Velocity_colm_size = Velocity_sparsity->getSizeColm();
  Velocity_findrm_size = Velocity_sparsity->getSizeFindrm();
  int numValsPerNode = state->getValsPerNode("Velocity");
  int numVectorEntries = state->getNodesPerEle("Velocity");
  numVectorEntries = numVectorEntries * numValsPerNode;
  int numMatrixEntries = numVectorEntries * numVectorEntries;
  cudaMalloc((void**)(&localVector), sizeof(double) * numEle * numVectorEntries);
  cudaMalloc((void**)(&localMatrix), sizeof(double) * numEle * numMatrixEntries);
  cudaMalloc((void**)(&globalVector), sizeof(double) * numNodes * numValsPerNode);
  cudaMalloc((void**)(&globalMatrix), sizeof(double) * Velocity_colm_size);
  cudaMalloc((void**)(&solutionVector), sizeof(double) * numNodes * numValsPerNode);
}

extern "C" void finalise_gpu_()
{
  delete state;
}

extern "C" void run_model_(double* dt_pointer)
{
  double dt = *dt_pointer;
  int numEle = state->getNumEle();
  int numNodes = state->getNumNodes();
  int* eleNodes = state->getEleNodes();
  int nodesPerEle = state->getNodesPerEle("Coordinate");
  int blockXDim = 64;
  int gridXDim = 128;
  double* CoordinateCoeff = state->getElementValue("Coordinate");
  A<<<gridXDim,blockXDim>>>(numEle, localMatrix, dt, CoordinateCoeff);
  double* VelocityCoeff = state->getElementValue("Velocity");
  RHS<<<gridXDim,blockXDim>>>(numEle, localVector, dt, CoordinateCoeff, VelocityCoeff);
  cudaMemset(globalMatrix, 0, sizeof(double) * Velocity_colm_size);
  cudaMemset(globalVector, 0, sizeof(double) * state->getValsPerNode("Velocity") * numNodes);
  matrix_addto<<<gridXDim,blockXDim>>>(Velocity_findrm, Velocity_colm, globalMatrix, eleNodes, localMatrix, numEle, nodesPerEle);
  vector_addto<<<gridXDim,blockXDim>>>(globalVector, eleNodes, localVector, numEle, nodesPerEle);
  cg_solve(Velocity_findrm, Velocity_findrm_size, Velocity_colm, Velocity_colm_size, globalMatrix, globalVector, numNodes, solutionVector);
  expand_data<<<gridXDim,blockXDim>>>(VelocityCoeff, solutionVector, eleNodes, numEle, state->getValsPerNode("Velocity"), nodesPerEle);
}

extern "C" void return_fields_()
{
  state->returnFieldToHost("Velocity");
}



