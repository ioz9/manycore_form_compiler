// Generated by the Manycore Form Compiler.
// https://github.com/gmarkall/manycore_form_compiler


#include "cudastatic.hpp"
#include "cudastate.hpp"


__global__ void a(int n_ele, double* localTensor, double dt, double* c0)
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
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          double ST0 = 0.0;
          ST0 += CG1[i_r_0][i_g] * CG1[i_r_1][i_g] * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]);
          localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] += ST0 * w[i_g];
        };
      };
    };
  };
}

__global__ void L(int n_ele, double* localTensor, double dt, double* c0, double* c1)
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
  double c_q1[6];
  double c_q0[6][2][2];
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      c_q1[i_g] = 0.0;
      for(int q_r_0 = 0; q_r_0 < 3; q_r_0++)
      {
        c_q1[i_g] += c1[i_ele + n_ele * q_r_0] * CG1[q_r_0][i_g];
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
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      localTensor[i_ele + n_ele * i_r_0] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        double ST1 = 0.0;
        ST1 += CG1[i_r_0][i_g] * c_q1[i_g] * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]);
        localTensor[i_ele + n_ele * i_r_0] += ST1 * w[i_g];
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
  state->extractField("Tracer", 0);
  state->allocateAllGPUMemory();
  state->transferAllFields();
}

extern "C" void finalise_gpu_()
{
  delete state;
}

extern "C" void run_model_(double* dt_pointer)
{
  double dt = *dt_pointer;
  int blockXDim = 64;
  int gridXDim = 128;
  double* localVector;
  double* localMatrix;
  double* globalVector;
  double* globalMatrix;
  double* solutionVector;
  CsrSparsity* Tracer_sparsity = state->getSparsity("Tracer");
  int* Tracer_colm = Tracer_sparsity->getCudaColm();
  int* Tracer_findrm = Tracer_sparsity->getCudaFindrm();
  int Tracer_colm_size = Tracer_sparsity->getSizeColm();
  int Tracer_findrm_size = Tracer_sparsity->getSizeFindrm();
  int Tracer_numEle = state->getNumEle("Tracer");
  int Tracer_numNodes = state->getNumNodes("Tracer");
  int* Tracer_eleNodes = state->getEleNodes("Tracer");
  int Tracer_nodesPerEle = state->getNodesPerEle("Tracer");
  int Tracer_numValsPerNode = state->getValsPerNode("Tracer");
  int Tracer_numVectorEntries = state->getNodesPerEle("Tracer");
  Tracer_numVectorEntries = Tracer_numVectorEntries * Tracer_numValsPerNode;
  cudaMalloc((void**)(&localMatrix), sizeof(double) * Tracer_numEle * Tracer_numVectorEntries * Tracer_numVectorEntries);
  double* CoordinateCoeff = state->getElementValue("Coordinate");
  a<<<gridXDim,blockXDim>>>(Tracer_numEle, localMatrix, dt, CoordinateCoeff);
  cudaMalloc((void**)(&globalMatrix), sizeof(double) * Tracer_colm_size);
  cudaMemset(globalMatrix, 0, sizeof(double) * Tracer_colm_size);
  matrix_addto<<<gridXDim,blockXDim>>>(Tracer_findrm, Tracer_colm, globalMatrix, Tracer_eleNodes, localMatrix, Tracer_numEle, Tracer_nodesPerEle);
  cudaFree(localMatrix);
  cudaMalloc((void**)(&localVector), sizeof(double) * Tracer_numEle * Tracer_numVectorEntries);
  double* TracerCoeff = state->getElementValue("Tracer");
  L<<<gridXDim,blockXDim>>>(Tracer_numEle, localVector, dt, CoordinateCoeff, TracerCoeff);
  cudaMalloc((void**)(&globalVector), sizeof(double) * Tracer_numNodes * Tracer_numValsPerNode);
  cudaMemset(globalVector, 0, sizeof(double) * Tracer_numValsPerNode * Tracer_numNodes);
  vector_addto<<<gridXDim,blockXDim>>>(globalVector, Tracer_eleNodes, localVector, Tracer_numEle, Tracer_nodesPerEle);
  cudaFree(localVector);
  cudaMalloc((void**)(&solutionVector), sizeof(double) * Tracer_numNodes * Tracer_numValsPerNode);
  cg_solve(Tracer_findrm, Tracer_findrm_size, Tracer_colm, Tracer_colm_size, globalMatrix, globalVector, Tracer_numNodes, solutionVector);
  cudaFree(globalMatrix);
  cudaFree(globalVector);
  expand_data<<<gridXDim,blockXDim>>>(TracerCoeff, solutionVector, Tracer_eleNodes, Tracer_numEle, Tracer_numValsPerNode, Tracer_nodesPerEle);
  cudaFree(solutionVector);
}

extern "C" void return_fields_()
{
  state->returnFieldToHost("Tracer");
}



