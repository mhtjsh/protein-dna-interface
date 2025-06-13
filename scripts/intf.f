C
C     INTF.F                                 June, 2000
c     by P. Chakrabarti
c
c     Program to fish out atoms in an interface in a complex. It
c     reads two NACCESS output (.asa) files -one for
c     a subunit (say, A) and the other for the subunit in a complex.
c     If the ASA of an atom in A is more than in the complex, it is
c     written out in the PDB format with the ASA values (in the
c     isolated molecule and in the complex) occupying the columns for
c     the occupancy and the temp-factor). 
c     **Note:  Modifications made: 
c     1) so that ASA(su)-ASA(complex) >= 0.1 for an atom to
c     be considered in the interface).
c     2) in some files like 1mkw, the residue numbering follows that
c     in chymotrypsin, so that there may be more than one residue with
c     the same res-no (say 60), but these are distinguished by putting
c     A, B, C, etc after the number. Now the program has an extra set of
c     variables (add_id and resid_) to take care of this.
c     The output file name has the extension .int, and the
c     name is the same as the complex (first four letters only)
c     with the subunit id (to be given as input) added.
c
c     Counts are given of the number of atoms and residues in the 
c     interface, as also those for atoms with zero accessibilities 
c     and the residues containing them. Two files are created:
c     inner.int and outer.int; the former contains residues with at
c     least one atom with zero ASA, the other contains the remaining
c     residues at the interface. (Results from different runs with new 
c     PDB files are appended to these). Format of these files:
c     record 1: PDB file name (with suunit id added), #s of atoms and
c     residues in the interface, # of atoms with zero ASA and # residues
c     with at least one such atom, # of atoms with non-zero ASA and the 
c     number of residues which have all interface atoms with nonzero ASA.
c     (The position of the last two pairs of entries are interchanged in
c     the two output files - inner.int will first have information for
c     the inner shell, followed by the outer shell; just the opposite
c     for the outer.int).
c     record 2: Name and # appropiate type of residues (10 residues/line).
c
c     **Problem located: 1) For some structures I have put two chains under
c     same ID. If it so happens that the each of these chains contribute a
c     residue with the same name and number, then these will be taken as the
c     single residue. So check if residue numbers in the inner and outer
c     shells add up to the total number. If not, find out the missing 
c     residue by checking the pdb_su.int file, and edit the inner/outer.int
c     files. (I think if both the residues go to the same shell, there is no
c     problem; only if they go to different shells, the one in the outer shell
c     will be lost).
c
      CHARACTER fil*30,rec*4
      character*4 label,atm,label1,atm1
      character*3 res,res1
      character*1 su_id,su,su1
      real x,y,z,asa,x1,y1,z1,asa1
      integer iatom,ires,iatom1,ires1
      integer n_atom,n_res,old_res_no      !to count interface atoms
      integer n_atom0,n_res0,old_res_no0      !to count atoms with ASA=0
      logical cycle
c     the following variables are to keep track of residues with
c     at least one atom with zero ASA, and the remaining residues in the
c     interface - to be used in the output files.
      integer ires_i(150),ires_i0(100),ires_in0(100),n_res_n0,n_atom_n0
      character*3 res_i(150),res_i0(100),res_in0(100)
      integer ibeg,iend,n_left,n          !for writing 10 res/line
      logical not_found
c     variables for modification 2:
      character*1 add_id,add_id1,old_add_id,old_add_id0
      character*1 resid_i(150),resid_i0(100)
c
      WRITE(6,100)
      read (5,110) fil
      OPEN(9,file=FIL,status='OLD',FORM='FORMATTED')
      read (5,110) fil
      OPEN(8,file=FIL,status='OLD',FORM='FORMATTED')
      write(6,115)
      read (5,145) su_id 
      rec(1:4)=fil(1:4)
      OPEN(9,file=rec//su_id//'.int',status='new',FORM='FORMATTED')
      OPEN(10,file='inner.int',access='append',FORM='FORMATTED')
      OPEN(11,file='outer.int',access='append',FORM='FORMATTED')
c
      cycle=.true.
      n_atom=0
      n_res=0
      old_res_no=0
      old_add_id=' '
      n_atom0=0
      n_res0=0
      old_res_no0=0
      old_add_id0=' '
c
      n_atom_n0=0
      n_res_n0=0
      do i=1,100
	ires_i0(i)=0
	ires_in0(i)=0
	res_i0(i)='   '
	res_in0(i)='   '
	resid_i0(i)=' '
      enddo
      do i=1,150
	ires_i(i)=0
	res_i(i)='   '
	resid_i(i)=' '
      enddo
c
      do while (cycle)
      read(7,120,end=170)LABEL,IATOM,ATM,RES,su,IRES,add_id,X,Y,Z,asa 
 500  READ(8,120,END=160) LABEL1,IATOM1,ATM1,RES1,su1,IRES1,add_id1,
     .                             x1,y1,z1,asa1
      if (su.eq.su1.and.res.eq.res1.and.ires.eq.ires1) then
c-the following line is changed to have the difference of two ASAs exceed 0.1
c       if(asa1.lt.asa) then
        if((asa-asa1).ge.0.1) then
	 write(9,125)  LABEL,IATOM,ATM,RES,su,IRES,add_id,X,Y,Z,
     .                 asa,asa1
	 n_atom=n_atom+1
	 if(ires1.ne.old_res_no.or.add_id1.ne.old_add_id) then
		n_res=n_res+1
		old_res_no=ires1
		old_add_id=add_id1
		res_i(n_res)=res1
		ires_i(n_res)=ires1
		resid_i(n_res)=add_id1
	 endif
c     count for the atoms with ASA=0, and # residues having such atoms
c-the following line is changed to have the difference of two ASAs exceed 0.1
c        if (asa1.eq.0.0) then
         if (asa1.eq.0.0.and.(asa-asa1).ge.0.1) then
           n_atom0=n_atom0+1
           if(ires1.ne.old_res_no0.or.add_id1.ne.old_add_id0) then
                n_res0=n_res0+1
                old_res_no0=ires1
		old_add_id0=add_id1
                res_i0(n_res0)=res1
                ires_i0(n_res0)=ires1
                resid_i0(n_res0)=add_id1
           endif
	 else
	   n_atom_n0=n_atom_n0+1
	 endif
c     end of count with ASA=0
	endif
      else
	goto 500
      endif
      enddo     ! end of the main do while loop
 170  write(6,130) n_atom,n_res
      write(6,135) n_atom0,n_res0
c     create 2 files: 1)residues with at least one atom with zero ASA, and 
c     2) the remaining residues
      do i=1,n_res           !use all interface residues
	not_found=.true.
	do j=1,n_res0        !residues with at least an atom of ASA=0
	  if(res_i(i).eq.res_i0(j).and.ires_i(i).eq.ires_i0(j).and.
     .              resid_i(i).eq.resid_i0(j))
     .    not_found=.false.
	enddo
	if (not_found) then
	  n_res_n0=n_res_n0 +1
	  res_in0(n_res_n0)=res_i(i)
	  ires_in0(n_res_n0)=ires_i(i)
	endif
      enddo
      write(10,155) rec//su_id,n_atom,n_res,n_atom0,n_res0,
     .              n_atom_n0,n_res_n0
      write(11,155) rec//su_id,n_atom,n_res,n_atom_n0,n_res_n0,
     .              n_atom0,n_res0
c**** write 10 residues per line
      iend=0      !to take care of cases when less than 10 residues are there
      n=(n_res0/10)
      do i=1,n
        ibeg=(i-1)*10+1
        iend=i*10
        write(10,165) (res_i0(j),ires_i0(j),j=ibeg,iend)
      enddo
      n_left=n_res0 - 10*n
      ibeg=iend+1
      iend=ibeg+n_left-1
      if (n_left.ne.0) then
        write(10,165) (res_i0(j),ires_i0(j),j=ibeg,iend)
      endif
c**** write 10 residues per line
      iend=0      !to take care of cases when less than 10 residues are there
      n=(n_res_n0/10)
      do i=1,n
        ibeg=(i-1)*10+1
        iend=i*10
        write(11,165) (res_in0(j),ires_in0(j),j=ibeg,iend)
      enddo
      n_left=n_res_n0 - 10*n
      ibeg=iend+1
      iend=ibeg+n_left-1
      if (n_left.ne.0) then
        write(11,165) (res_in0(j),ires_in0(j),j=ibeg,iend)
      endif
      stop ' ***Job Done***'
 160  stop ' ***atom records in the two files donot match***'
 100  FORMAT(' INPUT asa file-names (for subunit & complex:)')
 110  format(a30)
 115  format(' INPUT the subunit id (use small cap:)')
 120  FORMAT(A4,2X,I5,2X,A4,A3,1X,a1,I4,a1,3X,3F8.3,2x,2F6.2)
 125  FORMAT(A4,2X,I5,2X,A4,A3,1X,a1,I4,a1,3X,3F8.3,2F6.2)
 130  format(' No of interface atoms: ',9x,i5, 
     .       '  No of residues: ',5x,i5)
 135  format(' # Atoms with ASA=0 in complex:  ',i5,/,15x,
     .    ' # Residues containing at least one such atom:',i5)
 145  format(a1)
 155  format(1x,a5,3(2x,2i5))
 165  format(50(1x,a3,i4))
      end
